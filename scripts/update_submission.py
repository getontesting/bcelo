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

DEMO_URL = (
    "https://cdn.jsdelivr.net/gh/getontesting/bcelo@9716d09/docs/index.html"
)

DESCRIPTION = (
    "Agent Celo mainnet untuk pekerjaan nyata M RIFKI TRI ADITYA (freelance web3 developer): "
    "mengubah USD₮ menjadi stablecoin lokal lewat 5 koridor Textile FX RFQ "
    "(IDRX, cNGN, wBRL, wCOP) lalu membayar penerima di luar tim — 15 transaksi "
    "bertag celo_69fe50f9aa63 (agentId ERC-8004 10077). "
    "Juga login ke website biasa lewat Agent Vault tanpa password, "
    "membayar per-request via x402 (0xf72b3bf1... blok 83290930), "
    "dan memanggil layanan pihak ketiga di usebuy.ai (0xaa6b2919..., $0.01 USDT). "
    "Altana passkey wallet 0xBf39... dengan session key berscoped "
    "(0xffa9945f..., cap 0.001 CELO/hari, expiry 1 jam). "
    "Repo: https://github.com/getontesting/bcelo"
)

BASE: list[str] = ["npx.cmd", "--yes", "loopshouse", "project", "update",
                   "--event", "agents-open-for-business",
                   "--demo-url", DEMO_URL,
                   "--description", DESCRIPTION]
for bounty in BOUNTIES:
    BASE += ["--bounty-ids", bounty]

BASE += [
    "--answer",
    "x402 PayTo address="+'0x1B441d9002a7ED68e996aBE63bAd054802B2549B',
    "--answer",
    "Region=Indonesia",
    "--answer",
    "Public X post=https://x.com/CryptoBits03/status/2123859111054029181",
    "--answer",
    "buy transaction hashes="
    "0xaa6b2919729b0f695bf1dab2b2789f50e578984e12a98d0a8092a62081fc2f21 — "
    "paid call $0.01 USDT from agent to Chainstack Celo JSON-RPC via gateway.usebuy.ai, "
    "returned eth_chainId=0xa4ec (42220). Real third-party service, no Self proof required.",
    "--answer",
    "Stablecoin Corridors track details=Wallet 0x2Ff10a4748902E82E82835Edef6d98c306e4ba38. "
    "5 koridor aktif via Textile FX RFQ di Celo mainnet: USDT->IDRX (2x), USDT->cNGN, "
    "USDT->wBRL, USDT->wCOP. 5 putaran, 15 transaksi bertag celo_69fe50f9aa63 "
    "(approval+swap+payout). Swap/payout: "
    "IDRX 0xfadc5702.../0x85c03b3a..., "
    "cNGN 0xf127380e.../0xbf43879a..., "
    "IDRX 0x6f2b41db.../0xcce959b4..., "
    "wBRL 0xf8e9207a.../0x3988bf05..., "
    "wCOP 0x8d0af125.../0x24023a7b.... "
    "Semua payout ke user eksternal 0x6cd38eddeb7c0972a93056e20b8e1b11eb141eef.",
    "--answer",
    "Agent Vault: Online & Onchain Checkouts track details="
    "Agent Vault MCP (API key) dipakai untuk sign-in ke https://github.com/login "
    "dengan mock token av_login_github_username/password — agent tidak pernah melihat password asli. "
    "Bukti: fill_login filled=2/2, observe_page status=ok reason='accountControl; looks signed in'. "
    "Pembayaran onchain lewat x402: tx 0xf72b3bf1d7a6ce96b2c29b9b0dafb528ba0c5b0db8e425a6a9aba6f0eb29cd1e "
    "blok 83290930, $0.10 USDT ke /premium seller lokal. "
    "REAL USE: paid call ke layanan pihak ketiga di usebuy.ai (Chainstack Celo RPC) "
    "tx 0xaa6b2919729b0f695bf1dab2b2789f50e578984e12a98d0a8092a62081fc2f21, $0.01 USDT, "
    "response eth_chainId=0xa4ec. Spending rule: kartu tidak dipakai (test card), "
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
