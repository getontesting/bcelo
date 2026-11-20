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
    "Altana Agent Wallets track details="
    "Wallet (passkey, non-custodial): 0xBf39b7f2211128b5148d45eA28b4052349d2aBe0. "
    "Aktivasi onchain: 0x36f126e4a9f23aec7d7f96c9b48b477641efe25d7bbab26c4ca63a45cf163384 "
    "(blok 83294878, status sukses). "
    "Session key terdaftar di Keystore: 0xffa9945f8e0c23a9abb9a33b015858d0cedd1ee0fe2bc13d341e0b9e83985eaf. "
    "Policy: spend cap 0.001 CELO/hari, allowlist hanya wallet ini, expiry 1 jam, "
    "dapat dicabut dalam satu transaksi. "
    "Produk review: https://github.com/getontesting/bcelo/issues/1.",
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
