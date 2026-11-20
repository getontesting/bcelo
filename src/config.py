"""Konfigurasi dan konstanta Celo mainnet untuk entry hackathon."""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv
from eth_utils import to_checksum_address

load_dotenv()

CELO_MAINNET_CHAIN_ID = 42220

# Token Celo mainnet (dari halaman hackathon).
TOKENS = {
    "USDC": "0xcebA9300f2b948710d2653dD7B07f33A8B32118C",
    "USDT": "0x48065fbBE25f71C9282ddf5e1cD6D6A887483D5e",
    "CNGN": "0xF6829D7393dAe24509eb1E52eE8e572e2E271a4f",
    "IDRX": "0x18Bc5bcC660cf2B9cE3cd51a404aFe1a0cBD3C22",
    "WARS": "0x0DC4F92879B7670e5f4e4e6e3c801D229129D90D",
    "WBRL": "0xD76f5Faf6888e24D9F04Bf92a0c8B921FE4390e0",
    "WMXN": "0x337E7456B420bD3481e7FA61fA9850343d610d34",
    "WCOP": "0x8a1D45e102e886510e891d2Ec656a708991e2D76",
}
TEXTILE_REACTOR = "0xa9AA0a64769cBed4d3B1Ceb4Df01CdE915C235b3"


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Environment variable wajib belum diisi: {name}")
    return value


def _addr(name: str, default: str = "") -> str:
    raw = os.getenv(name, default).strip()
    if not raw:
        raise ValueError(f"Alamat belum diisi: {name}")
    return to_checksum_address(raw)


@dataclass(frozen=True)
class Settings:
    private_key: str
    payout_address: str
    attribution_code: str
    github_repo: str
    rpc_url: str
    chain_id: int
    textile_api_url: str
    textile_api_key: str | None
    sell_token: str
    buy_token: str
    sell_amount: int
    recipient: str

    @classmethod
    def from_env(cls) -> "Settings":
        api_key = os.getenv("TEXTILE_API_KEY", "").strip() or None
        return cls(
            private_key=_required("TAKER_PRIVATE_KEY"),
            payout_address=_addr("PAYOUT_ADDRESS"),
            attribution_code=_required("ATTRIBUTION_CODE"),
            github_repo=os.getenv("GITHUB_REPO", "").strip(),
            rpc_url=os.getenv("CELO_RPC_URL", "https://forno.celo.org").strip(),
            chain_id=int(os.getenv("CHAIN_ID", str(CELO_MAINNET_CHAIN_ID))),
            textile_api_url=os.getenv(
                "TEXTILE_API_URL", "https://api.textilecredit.com/v2"
            ).strip(),
            textile_api_key=api_key,
            sell_token=_addr("SELL_TOKEN", TOKENS["USDT"]),
            buy_token=_addr("BUY_TOKEN", TOKENS["IDRX"]),
            sell_amount=int(os.getenv("SELL_AMOUNT_ATOMIC", "10000000")),
            recipient=_addr("RECIPIENT_ADDRESS"),
        )
