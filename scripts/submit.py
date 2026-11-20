"""Kirim submission Loops House.

Jalankan tanpa argumen untuk melihat draft, lalu dengan --confirm untuk mengirim.
Keputusan submit harus dibuat oleh builder (bukan agent).
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent.parent
VALUES = dotenv_values(ROOT / ".env")
PAY = (VALUES.get("PAYOUT_ADDRESS") or "").strip()

BASE = [
    "npx.cmd", "--yes", "loopshouse", "project", "create",
    "--event", "agents-open-for-business",
    "--name", "Celo Corridor Agent",
    "--tagline", "Agent membayar supplier IDRX via Textile FX dan x402 di Celo mainnet",
    "--description",
    "Agent Celo mainnet: konversi USDT ke IDRX via Textile FX RFQ lalu bayar penerima "
    "dengan attribution tag di setiap transaksi; plus x402 per-request pakai USDT. "
    "Bukti: ERC-8004 agentId 10077, tag celo_624f9418a842, swap 0xc9733ab20c59c7629a4357dfcddbb47c4c5282fc32dacc56d323fda7338076e0, "
    "payout 0xc7fa464678206c5d6bcb756acd2a55b1b4ad5881c770808f852800840d827578, "
    "x402 0xf72b3bf1d7a6ce96b2c29b9b0dafb528ba0c5b0db8e425a6a9aba6f0eb29cd1e blok 83290930.",
    "--repo-url", "https://github.com/getontesting/bcelo",
    "--demo-url", "https://github.com/getontesting/bcelo",
    "--logo", str(ROOT / "assets" / "logo.png"),
    "--screenshot", str(ROOT / "assets" / "verified-activity.png"),
    "--bounty-ids", "7527f91b-899a-484b-a87f-5314e21bb45d",
    "--bounty-ids", "4379f770-3b52-4bb9-93cf-a2853765658f",
    "--answer", "Agent wallet=" + PAY,
    "--answer", "Team contacts=getontesting, getontesting@gmail.com",
    "--answer", "Payout wallet on Celo=" + PAY,
    "--answer", "ERC-8004 agent ID=10077",
    "--answer", "Self Agent ID (mainnet agentId)=not registered - no supported passport",
    "--answer", "Attribution tag=celo_624f9418a842",
    "--answer",
    "Named user=Penerima uji IDRX 0x9D7801B3aA68be61B8ff888a91f038D00b1E6A01; "
    "pekerjaan: pembayaran jasa/supplier dalam IDRX. Data sementara, akan diganti user bernama.",
    "--answer", "x402 PayTo address=SELLER_PAY_TO di .env (dompet seller terpisah)",
    "--answer", "Stablecoin Corridors track details=USDT->IDRX via Textile FX; swap 0xc9733ab2...; payout 0xc7fa4646...",
    "--answer", "Agent Vault: Online & Onchain Checkouts track details=x402 tx 0xf72b3bf1... blok 83290930, $0.10 USDT",
    "--answer", "Founder and/or Project Handles on X=https://x.com/CryptoBits03",
    "--answer", "Follow @Celo and @CeloDevs on X=yes, following both @Celo and @CeloDevs",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", action="store_true", help="benar-benar kirim")
    parser.add_argument("--video-url", default="", help="URL video demo (field wajib)")
    args = parser.parse_args()

    cmd = list(BASE)
    if args.video_url:
        cmd += ["--video-url", args.video_url]
    if args.confirm:
        cmd.append("--confirm")

    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=240)
    print(result.stdout[-12000:])
    if result.stderr:
        print("STDERR:", result.stderr[-1500:])


if __name__ == "__main__":
    main()
