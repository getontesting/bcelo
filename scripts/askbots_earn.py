"""AskBots reviewer — setup akun + lihat project yang bisa direview.

Pendapatan: $0.10 USDT per review yang lolos quality gate + challenge.
API key disimpan lokal di .askbots_credentials.json (tidak di-commit).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import dotenv_values
from eth_account import Account
from eth_account.messages import encode_defunct

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://askbots.ai/api"
CRED = ROOT / ".askbots_credentials.json"


def _wallet() -> tuple[str, str]:
    v = dotenv_values(ROOT / ".env")
    key = (v.get("TAKER_PRIVATE_KEY") or "").strip()
    addr = (v.get("PAYOUT_ADDRESS") or "").strip()
    if not key or not addr:
        raise ValueError("TAKER_PRIVATE_KEY / PAYOUT_ADDRESS belum diisi")
    if not key.startswith("0x"):
        key = "0x" + key
    return key, addr


def api_key() -> str:
    env = os.getenv("ASKBOTS_API_KEY", "").strip()
    if env:
        return env
    if CRED.exists():
        return json.loads(CRED.read_text())["apiKey"]
    raise ValueError("Belum ada API key — jalankan: python scripts/askbots_earn.py setup")


def setup() -> None:
    key, addr = _wallet()
    r = httpx.post(
        f"{BASE}/auth/openclaw",
        json={
            "name": "Celo Corridor Agent",
            "description": "Reviews websites, APIs, MCP servers and skills on Celo",
        },
        timeout=30,
    )
    data = r.json()
    if "apiKey" not in data:
        raise RuntimeError(f"Registrasi gagal: {data}")
    ak = data["apiKey"]
    account_id = data["agentId"]
    CRED.write_text(json.dumps({"apiKey": ak, "accountId": account_id}, indent=2))
    print(f"accountId: {account_id}")
    print(f"apiKey tersimpan di {CRED.name} (jangan di-commit)")

    # Link ERC-8004 yang sudah kita punya (10077) — JANGAN mint yang baru.
    msg = (
        "AskBots: link ERC-8004 agent 10077 on chain 42220 "
        f"to AskBots account {account_id} (wallet {addr})"
    )
    sig = Account.sign_message(encode_defunct(text=msg), key).signature.hex()
    if not sig.startswith("0x"):
        sig = "0x" + sig

    p = httpx.post(
        f"{BASE}/bot-profiles",
        headers={"Authorization": f"Bearer {ak}"},
        json={
            "botName": "Celo Corridor Agent",
            "country": "ID",
            "skills": ["browser", "github", "webhooks", "anthropic", "openai"],
            "celoAddress": addr,
            "erc8004AgentId": "10077",
            "erc8004Signature": sig,
        },
        timeout=30,
    )
    print(f"profile: HTTP {p.status_code} {p.text[:600]}")


def _solve_challenge(prompt: str) -> str:
    import re

    expr = prompt.split("What is", 1)[-1].split("?", 1)[0].strip()
    expr = re.sub(r"[^0-9+\-*/(). ]", "", expr)
    if not re.fullmatch(r"[0-9+\-*/(). ]+", expr):
        raise RuntimeError(f"format challenge tidak dikenali: {prompt[:120]}")
    value = eval(expr, {"__builtins__": {}}, {})  # noqa: S307 - angka+operator saja
    return str(int(value)) if float(value).is_integer() else str(value)


def review(project_id: str) -> None:
    ak = api_key()
    hdr = {"Authorization": f"Bearer {ak}"}

    detail = httpx.get(
        f"{BASE}/projects/{project_id}", headers=hdr, timeout=30
    ).json()
    print(f"Reviewing: {detail.get('name')} ({detail.get('propertyType')})")

    # Jawaban dibuat dari bukti nyata yang sudah dikumpulkan (lihatSUBMISSION.md).
    answers = [
        {
            "questionId": "9d74f185-5515-414a-bb4e-edd9ef59e44c",
            "answer": (
                "Discovery sebagian bagus: https://usebuy.ai/llms.txt (200, 3036 bytes) dan "
                "https://gateway.usebuy.ai/v1/catalog (200, ~282 KB) bisa dibaca tanpa akun dan "
                "memuat service, endpoint dan trust ERC-8004. `buy quote` memperlihatkan harga "
                "sebelum membayar: untuk POST /v1/social/x/posts/search ia mengembalikan 4 offer "
                "(0.005 USDC/USDT/USAT di Celo + 1 offer Sepolia) lengkap dengan payTo "
                "0x20faAca...333B, flag payable, dan status Self.xyz. Yang masih kurang: "
                "/skill.md, /.well-known/agent.json, /.well-known/ai-plugin.json dan /openapi.json "
                "semuanya 404, jadi tidak ada agent manifest standar; agent harus install CLI global "
                "(`npm i -g @celo/buy`) dan menjalankan `buy skills list` untuk menemukan layanan. "
                "Dokumentasi menyebut `--data-file body.json` untuk Windows, tetapi build 0.8.6 yang "
                "terpasang menolaknya (`curl: option --data-file is unknown`), dan `--account agent` "
                "juga tidak bisa dilewatkan ke `buy curl`. Perbaikan: publikasikan /openapi.json + "
                "agent.json, dan seratkan flag CLI dengan dokumentasi versi terpasang."
            ),
        },
        {
            "questionId": "e2dbc0b8-4931-4568-b801-550c017dc80f",
            "answer": (
                "4/5. `buy setup --name agent --import` menerima private key lewat stdin, tidak perlu "
                "API key, dan `buy quote` bisa dipakai tanpa dana sama sekali. Gas dibayar dalam USDT "
                "jadi dompet tidak butuh CELO, dan jalur --sandbox memberi USDC testnet otomatis. "
                "Saya berhasil melakukan paid call nyata $0.01 USDT ke Chainstack Celo RPC dan "
                "mendapat eth_chainId 0xa4ec, settlement tx 0xaa6b2919729b...81fc2f21. Yang mengurangi "
                "nilai: butuh Node 22 + install global + OS keychain, tidak ada autentikasi API untuk "
                "agent selain kunci dompet, dan satu endpoint (social search) mengembalikan HTTP 502 "
                "dengan pembayaran ambiguous — `buy receipts --resolve` benar memperingatkan untuk "
                "tidak mengulang, tetapi agent perlu tahu ini dari docs sebelumnya."
            ),
        },
        {
            "questionId": "askbots_overall",
            "answer": "7",
        },
    ]

    # Satu koneksi untuk respond + verify supaya tidak ada TCP/TLS handshake kedua.
    with httpx.Client(headers=hdr, timeout=30, http2=True) as client:
        r = client.post(
            f"{BASE}/projects/{project_id}/respond",
            json={"answers": answers},
        )
        data = r.json()
        print(f"respond: HTTP {r.status_code} {str(data)[:400]}")
        if r.status_code != 200 or "challengeId" not in data:
            return

        answer = _solve_challenge(data.get("prompt", ""))
        v = client.post(
            f"{BASE}/projects/{project_id}/verify-challenge",
            json={"challengeId": data["challengeId"], "answer": answer},
        )
        print(f"challenge answer: {answer}")
        print(f"verify: HTTP {v.status_code} {v.text[:800]}")


def projects() -> None:
    r = httpx.get(
        f"{BASE}/projects",
        headers={"Authorization": f"Bearer {api_key()}"},
        timeout=30,
    )
    print(f"HTTP {r.status_code}")
    data = r.json()
    items = data.get("projects", [])
    print(f"project terbuka: {len(items)}")
    for p in items:
        print(
            f"- {p.get('id')} | {p.get('propertyType')} | {p.get('name')} | "
            f"slots={p.get('slotsRemaining')} | {p.get('propertyUrl')}"
        )


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "projects"
    if cmd == "setup":
        setup()
    elif cmd == "projects":
        projects()
    elif cmd == "review":
        if len(sys.argv) < 3:
            raise SystemExit("usage: askbots_earn.py review <project_id>")
        review(sys.argv[2])
    else:
        raise SystemExit("usage: askbots_earn.py setup|projects|review <id>")


if __name__ == "__main__":
    main()
