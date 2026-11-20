"""Menjalankan seller x402 lokal supaya agent punya endpoint berbayar nyata."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

SIDECARS = Path(__file__).resolve().parent.parent / "sidecars"


def serve(port: int = 3402, *, dry_run: bool = False) -> None:
    env = os.environ.copy()
    env["X402_SELLER_PORT"] = str(port)
    env.setdefault("PAYOUT_ADDRESS", os.getenv("PAYOUT_ADDRESS", ""))

    if dry_run:
        print(f"[DRY-RUN] node x402-seller.mjs (port {port}, Celo mainnet)")
        return

    if "X402_API_KEY" not in env or not env["X402_API_KEY"].strip():
        raise ValueError(
            "X402_API_KEY belum diisi. Buat di https://x402.celo.org "
            "(connect wallet + Sign in with GitHub untuk credit mainnet)."
        )
    if not env.get("PAYOUT_ADDRESS"):
        raise ValueError("PAYOUT_ADDRESS belum diisi")

    subprocess.run(
        ["node", "x402-seller.mjs"],
        cwd=SIDECARS,
        env=env,
        check=True,
    )
