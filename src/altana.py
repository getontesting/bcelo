"""Track 4 — Altana session key (spend cap + allowlist + expiry).

Python menyiapkan calldata bertag, lalu sidecar TypeScript yang menjalankan
grantSession -> execute -> revokeSession lewat SDK resmi Altana.
"""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from eth_utils import to_checksum_address

from . import erc20
from .attribution import append_tag
from .config import TOKENS

SIDECARS = Path(__file__).resolve().parent.parent / "sidecars"


@dataclass
class AltanaResult:
    wallet: str
    status: str
    tx_hash: str
    revoked: bool
    fund_hash: str | None = None


def run(
    *,
    to: str,
    calldata: str,
    recipient: str,
    amount: int,
    attribution_code: str,
    allowed_contracts: list[str] | None = None,
    spend_limit: int = 1_000_000,
    expiry_seconds: int = 86_400,
    revoke: bool = True,
    dry_run: bool = False,
) -> AltanaResult | None:
    if not allowed_contracts:
        allowed_contracts = [to]

    tagged = append_tag(calldata, [attribution_code])
    if dry_run:
        print(f"[DRY-RUN] Altana grantSession -> execute -> revoke")
        print(f"[DRY-RUN] allowlist = {allowed_contracts}")
        print(f"[DRY-RUN] spend cap = {spend_limit}/hari, expiry = {expiry_seconds}s")
        print(f"[DRY-RUN] call to {to}, tagged calldata = {tagged[:66]}...")
        return None

    if "ALTANA_ADMIN_PRIVATE_KEY" not in os.environ:
        raise ValueError("ALTANA_ADMIN_PRIVATE_KEY belum diisi di .env")

    env = os.environ.copy()
    env.update(
        {
            "ALTANA_CALL_TO": to_checksum_address(to),
            "ALTANA_CALL_DATA": tagged,
            "ALTANA_ALLOWED_CONTRACTS": ",".join(
                to_checksum_address(c) for c in allowed_contracts
            ),
            "ALTANA_SPEND_LIMIT": str(spend_limit),
            "ALTANA_EXPIRY_SECONDS": str(expiry_seconds),
            "ALTANA_REVOKE": "1" if revoke else "0",
        }
    )

    proc = subprocess.run(
        ["bun", "run", "altana-agent-wallet.ts"],
        cwd=SIDECARS,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if proc.returncode != 0:
        if proc.stdout:
            print(f"[STDOUT] {proc.stdout[-2000:]}")
        raise RuntimeError(f"Altana sidecar gagal: {proc.stderr[-3000:]}")
    data = json.loads(proc.stdout)
    return AltanaResult(
        wallet=data["wallet"],
        status=str(data["status"]),
        tx_hash=data["txHash"],
        revoked=bool(data["revoked"]),
        fund_hash=data.get("fundHash"),
    )


def transfer_calldata(token: str, recipient: str, amount: int) -> str:
    return erc20.encode_transfer(token, recipient, amount)
