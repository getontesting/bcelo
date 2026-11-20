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
    "Stablecoin Corridors track details=Wallet 0x2Ff10a4748902E82E82835Edef6d98c306e4ba38. "
    "Koridor: USDT->IDRX dan USDT->cNGN via Textile FX RFQ di Celo mainnet. "
    "3 putaran konversi bertag celo_69fe50f9aa63, masing-masing approval+swap+payout: "
    "IDRX swap 0xfadc5702d58a64c048b56316ad7731692305bd951544517479815833e2b2f955 payout 0x85c03b3ad8ca8f72e0bc94ad0eb3c60a518efe238ae76e5f4f5ec11268520474; "
    "cNGN swap 0xf127380e1ced32795356a7a790ec02189f46c05f5464ed178ade8b821aca9bf5 payout 0xbf43879aa64748a5e618815cf3c3ed4461936eaa83653212da3806c08ebdb938; "
    "IDRX swap 0x6f2b41dba7ff712c4c0b985c7b4447533afaf638c932add92bb6412cac3ba59d payout 0xcce959b492afc755fa1b66f2b9f3516c2ed5b39b4b3f88728def4164b997cb30. "
    "Semua payout ke user eksternal 0x6cd38eddeb7c0972a93056e20b8e1b11eb141eef.",
    "--answer",
    "Agent Vault: Online & Onchain Checkouts track details="
    "Agent Vault MCP (API key) dipakai untuk sign-in ke https://github.com/login "
    "dengan mock token av_login_github_username/password — agent tidak pernah melihat password asli. "
    "Bukti: fill_login filled=2/2, observe_page status=ok reason='accountControl; looks signed in'. "
    "Pembayaran onchain lewat x402: tx 0xf72b3bf1d7a6ce96b2c29b9b0dafb528ba0c5b0db8e425a6a9aba6f0eb29cd1e "
    "blok 83290930, $0.10 USDT. Spending rule: kartu tidak dipakai (test card), "
    "x402 dibatasi $1/payment lewat spendControls.",
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
