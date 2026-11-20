"""Track 2 — Agent Vault sign-in lewat MCP server resminya.

Agent Vault melarang fill lewat HTTP biasa: field diisi lewat proxy WebSocket,
dan klien yang didukung adalah MCP server / Playwright SDK. Di sini kita
menjalankan MCP server resmi sebagai subprocess stdio dari Python.
"""
from __future__ import annotations

import asyncio
import os
import re
from dataclasses import dataclass

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

INSTALL_URL = "https://app.agentvault.io/mcp/agentvault-mcp.tgz"
_SESSION_RE = re.compile(r"(?:session:\s*|\"session\"\s*:\s*\")(s_[A-Za-z0-9_-]+)")


@dataclass
class SignInResult:
    session: str
    catalog: str
    fill: str
    outcome: str
    report: str
    observed: str = ""


def _text(result) -> str:
    return "\n".join(
        block.text for block in result.content if getattr(block, "text", None)
    )


def _handle(text: str) -> str | None:
    match = _SESSION_RE.search(text)
    return match.group(1) if match else None


def _server_params() -> StdioServerParameters:
    required = {
        "SELF_AGENT_PAY_API_KEY": "AGENTVAULT_API_KEY",
        "SELF_AGENT_PAY_PROXY_URL": "AGENTVAULT_PROXY_URL",
        "SELF_AGENT_PAY_API_URL": "AGENTVAULT_API_URL",
    }
    env = dict(os.environ)
    for target, source in required.items():
        value = os.getenv(source, "").strip()
        if not value:
            raise ValueError(f"{source} belum diisi di .env")
        env[target] = value

    return StdioServerParameters(
        command="npx",
        args=["-y", "--allow-remote=all", INSTALL_URL],
        env=env,
    )


async def _call(
    session: ClientSession, name: str, args: dict, handle: str | None
) -> str:
    payload = dict(args)
    if handle:
        payload["session"] = handle
    result = await session.call_tool(name, payload)
    text = _text(result)
    if getattr(result, "isError", False):
        raise RuntimeError(f"{name} ditolak: {text[:1000]}")
    return text


async def _run(args: dict, *, dry_run: bool) -> SignInResult | None:
    if dry_run:
        print("[DRY-RUN] urutan MCP: get_token_catalog -> open_page -> "
              "fill_login -> click -> get_session_outcome -> get_run_report "
              "-> close_session")
        return None

    params = _server_params()
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # get_token_catalog memulai session, baca katalog dulu.
            catalog = await _call(session, "get_token_catalog", {}, None)
            handle = _handle(catalog)

            opened = await _call(session, "open_page", {"url": args["url"]}, handle)
            handle = _handle(opened) or handle

            fill = await _call(
                session,
                "fill_login",
                {
                    "usernameSelector": args["username_selector"],
                    "usernameToken": args["username_token"],
                    "passwordSelector": args["password_selector"],
                    "passwordToken": args["password_token"],
                },
                handle,
            )

            await _call(
                session,
                "click",
                {"selector": args["submit_selector"]},
                handle,
            )

            outcome = await _call(
                session,
                "get_session_outcome",
                {
                    "successSelector": args["success_selector"],
                    "failureSelector": args.get("failure_selector", ".error"),
                    "timeout": 15000,
                },
                handle,
            )
            observed = await _call(session, "observe_page", {}, handle)
            report = await _call(session, "get_run_report", {}, handle)
            await _call(session, "close_session", {}, handle)

            return SignInResult(
                handle or "", catalog, fill, outcome, report, observed
            )


def list_tokens() -> str:
    """Cetak token catalog Agent Vault (mock token untuk login/card)."""
    async def _run_catalog() -> str:
        params = _server_params()
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await _call(session, "get_token_catalog", {}, None)

    return asyncio.run(_run_catalog())


def sign_in(
    *,
    url: str,
    username_selector: str,
    username_token: str,
    password_selector: str,
    password_token: str,
    submit_selector: str,
    success_selector: str,
    failure_selector: str = ".error",
    dry_run: bool = False,
) -> SignInResult | None:
    """Login ke website biasa memakai mock token Agent Vault."""
    return asyncio.run(
        _run(
            {
                "url": url,
                "username_selector": username_selector,
                "username_token": username_token,
                "password_selector": password_selector,
                "password_token": password_token,
                "submit_selector": submit_selector,
                "success_selector": success_selector,
                "failure_selector": failure_selector,
            },
            dry_run=dry_run,
        )
    )
