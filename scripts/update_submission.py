"""Tambahkan semua bounty non-paspor ke submission yang sudah ada.

Jalankan tanpa argumen untuk draft, dengan --confirm untuk menyimpan.
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BOUNTIES = [
    "7527f91b-899a-484b-a87f-5314e21bb45d",  # Stablecoin Corridors 1st
    "2cc35384-b522-46f8-906d-e02afd62b1bf",  # Stablecoin Corridors 2nd
    "08ad9cde-13cd-4d3c-a92c-104758a2bff1",  # Stablecoin Corridors 3rd
    "4379f770-3b52-4bb9-93cf-a2853765658f",  # Agent Vault 1st
    "ddee9cee-4065-43cd-a43b-c74aa9b55e74",  # Agent Vault 2nd
    "8e75a6d8-8da4-483d-82bf-2274df0356f0",  # Altana 1st
    "ab7df96f-e99d-45f7-ac41-fc9d7473af83",  # Altana 2nd
    "d7be31a0-9388-48bc-9943-1d32c697cb69",  # Altana product review (XP)
]

BASE: list[str] = ["npx.cmd", "--yes", "loopshouse", "project", "update",
                   "--event", "agents-open-for-business"]
for bounty in BOUNTIES:
    BASE += ["--bounty-ids", bounty]

BASE += [
    "--answer",
    "Altana Agent Wallets track details=Product review: "
    "https://github.com/getontesting/bcelo/issues/1. "
    "Policy disiapkan: spend cap 1 USDT/hari, allowlist USDT, expiry 24 jam, "
    "revoke otomatis. grantSession di Celo mainnet gagal di relay "
    "(RPC Request failed, code 3, data 0x) walau wallet sudah di-danai USDT + CELO.",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args()
    cmd = list(BASE) + (["--confirm"] if args.confirm else [])
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=180)
    print(result.stdout[-8000:])
    if result.stderr:
        print("STDERR:", result.stderr[-1200:])


if __name__ == "__main__":
    main()
