"""Track 2 — pembayaran x402 lewat sidecar resmi @x402/fetch."""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

SIDECARS = Path(__file__).resolve().parent.parent / "sidecars"


@dataclass
class X402Result:
    status: int
    body: str
    payment: dict | None


def pay(url: str, *, dry_run: bool = False) -> X402Result | None:
    """Bayar endpoint x402. Buyer tidak butuh API key facilitator, cuma USDC."""
    if dry_run:
        print(f"[DRY-RUN] x402 GET {url} (Celo mainnet, USDC)")
        return None

    if "BUYER_PRIVATE_KEY" not in os.environ:
        raise ValueError("BUYER_PRIVATE_KEY belum diisi di .env")
    if not SIDECARS.joinpath("x402-buyer.mjs").exists():
        raise FileNotFoundError("sidecars/x402-buyer.mjs tidak ditemukan")

    env = os.environ.copy()
    env.setdefault("CELO_RPC_URL", "https://forno.celo.org")
    if "X402_API_KEY" in env:
        # Diteruskan kalau kita juga menjalankan seller di mesin yang sama.
        pass

    proc = subprocess.run(
        ["node", "x402-buyer.mjs", url],
        cwd=SIDECARS,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"x402 sidecar gagal: {proc.stderr[-2000:]}")
    data = json.loads(proc.stdout)
    return X402Result(
        status=int(data["status"]),
        body=data.get("body", ""),
        payment=data.get("payment"),
    )
