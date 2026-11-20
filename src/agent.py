"""Alur Track 1: USD₮ -> IDRX via Textile FX, lalu bayar penerima eksternal.

Setiap transaksi yang dikirim di sini diberi attribution tag sebelum broadcast.
Hanya Celo mainnet yang dihitung oleh hackathon.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone

from web3 import Web3, HTTPProvider
from eth_utils import to_checksum_address

from . import erc20
from .attribution import append_tag, code_from_repo, verify_tx
from .config import CELO_MAINNET_CHAIN_ID, Settings
from .textile import TextileClient


def txhash(raw: object) -> str:
    value = raw.hex() if hasattr(raw, "hex") else str(raw)
    return value if str(value).startswith("0x") else "0x" + str(value)


def check_settings(settings: Settings, taker: str) -> list[str]:
    """Validasi cepat sebelum mengirim uang. Return daftar peringatan."""
    if settings.chain_id != CELO_MAINNET_CHAIN_ID:
        raise ValueError("Hanya Celo mainnet (chainId 42220) yang dihitung.")
    if taker.lower() == settings.recipient.lower():
        raise ValueError("Recipient tidak boleh sama dengan wallet agent.")
    if settings.sell_token.lower() == settings.buy_token.lower():
        raise ValueError("sellToken dan buyToken harus berbeda.")

    warnings: list[str] = []
    if settings.attribution_code == "celo_test1234":
        warnings.append(
            "ATTRIBUTION_CODE masih placeholder — ganti dengan kode yang "
            "diberikan saat enroll sebelum transaksi dihitung."
        )
    if settings.github_repo and "owner/" not in settings.github_repo:
        derived = code_from_repo(settings.github_repo)
        if derived != settings.attribution_code:
            warnings.append(
                f"Kode dari GITHUB_REPO = {derived}, tetapi ATTRIBUTION_CODE = "
                f"{settings.attribution_code}. Cek lagi kode dari enrollment."
            )
    return warnings


def send_tagged(
    w3: Web3, private_key: str, *, to: str, data: str, value: int = 0
) -> str:
    """Bangun, tandatangani, dan kirim transaksi mainnet."""
    account = w3.eth.account.from_key(private_key)
    tx: dict = {
        "chainId": w3.eth.chain_id,
        "nonce": w3.eth.get_transaction_count(account.address, "pending"),
        "from": account.address,
        "to": to_checksum_address(to),
        "data": data,
        "value": value,
    }
    tx["gas"] = w3.eth.estimate_gas(tx)
    base_fee = w3.eth.get_block("latest")["baseFeePerGas"]
    tip = w3.eth.to_wei(1, "gwei")
    tx["maxPriorityFeePerGas"] = tip
    tx["maxFeePerGas"] = base_fee * 2 + tip

    signed = w3.eth.account.sign_transaction(tx, private_key)
    raw = getattr(signed, "raw_transaction", None)
    if raw is None:
        raw = signed.rawTransaction  # web3 v6 compatibility
    return txhash(w3.eth.send_raw_transaction(raw))


@dataclass
class PaymentResult:
    quote: dict
    approval_hash: str | None
    swap_hash: str
    payout_hash: str
    verified: list[dict]


def pay_supplier(settings: Settings, *, dry_run: bool = False) -> PaymentResult | None:
    """Jalankan seluruh alur Track 1."""
    w3 = Web3(HTTPProvider(settings.rpc_url))
    account = w3.eth.account.from_key(settings.private_key)
    taker = to_checksum_address(account.address)

    warnings = check_settings(settings, taker)
    for item in warnings:
        print(f"[WARN] {item}")

    code = settings.attribution_code
    print(f"[INFO] taker                = {taker}")
    print(f"[INFO] chain                = {w3.eth.chain_id}")
    print(f"[INFO] attribution code     = {code}")
    print(f"[INFO] sell {settings.sell_amount} -> {settings.buy_token}")
    print(f"[INFO] recipient            = {settings.recipient}")

    with TextileClient(settings.textile_api_url, settings.textile_api_key) as client:
        quote = client.request_quote(
            chain_id=settings.chain_id,
            sell_token=settings.sell_token,
            buy_token=settings.buy_token,
            sell_amount=settings.sell_amount,
            taker=taker,
            private_key=settings.private_key,
        )
        q = quote["quote"]
        txns = quote["transactions"]
        required = int(q["takerPays"])
        reactor = to_checksum_address(q["reactor"])

        print(f"[INFO] rfqId                = {quote['rfqId']}")
        print(f"[INFO] takerPays            = {required}")
        print(f"[INFO] buyAmount            = {q['buyAmount']}")
        print(f"[INFO] reactor              = {reactor}")
        print(f"[INFO] expiresAt            = {q['expiresAt']}")

        if dry_run:
            print("[INFO] dry-run: tidak ada transaksi yang dikirim.")
            return None

        # --- 1. Approval sell token ke reactor (kalau belum cukup) ---
        approval_hash: str | None = None
        current = erc20.allowance(w3, settings.sell_token, taker, reactor)
        if current < required:
            if current > 0:
                # Token model USDT menolak approve(nonzero -> nonzero), reset dulu.
                reset_data = erc20.encode_approve(settings.sell_token, reactor, 0)
                reset_hash = send_tagged(
                    w3, settings.private_key,
                    to=settings.sell_token, data=append_tag(reset_data, [code]),
                )
                print(f"[INFO] reset allowance     = {reset_hash}")
                w3.eth.wait_for_transaction_receipt(reset_hash, timeout=180)

            approval_data = append_tag(txns["approval"]["data"], [code])
            approval_hash = send_tagged(
                w3, settings.private_key,
                to=txns["approval"]["to"], data=approval_data,
            )
            print(f"[INFO] approval tx          = {approval_hash}")
            receipt = w3.eth.wait_for_transaction_receipt(approval_hash, timeout=180)
            if receipt["status"] != 1:
                raise RuntimeError("Approval gagal onchain")
        else:
            print("[INFO] allowance sudah cukup, skip approval")

        # --- 2. Cek ulang deadline sebelum swap ---
        expires_at = datetime.fromisoformat(q["expiresAt"].replace("Z", "+00:00"))
        if datetime.now(timezone.utc) >= expires_at:
            raise RuntimeError("Quote expired saat approval — minta quote baru.")

        # --- 3. Swap (variabel kunci: pakai transactions.swap, BUKAN encodedOrder) ---
        swap_data = append_tag(txns["swap"]["data"], [code])
        swap_hash = send_tagged(
            w3, settings.private_key, to=txns["swap"]["to"], data=swap_data
        )
        print(f"[INFO] swap tx              = {swap_hash}")
        receipt = w3.eth.wait_for_transaction_receipt(swap_hash, timeout=180)
        if receipt["status"] != 1:
            raise RuntimeError("Swap gagal onchain")

        # --- 4. Bayar penerima eksternal dalam stablecoin lokal ---
        payout_data = erc20.encode_transfer(
            settings.buy_token, settings.recipient, int(q["buyAmount"])
        )
        payout_hash = send_tagged(
            w3, settings.private_key,
            to=settings.buy_token, data=append_tag(payout_data, [code]),
        )
        print(f"[INFO] payout tx            = {payout_hash}")
        receipt = w3.eth.wait_for_transaction_receipt(payout_hash, timeout=180)
        if receipt["status"] != 1:
            raise RuntimeError("Payout gagal onchain")

        # --- 5. Laporkan hash ke Textile (courtesy) ---
        try:
            client.submit(quote["rfqId"], quote["claimToken"], swap_hash)
        except Exception as exc:  # tidak boleh menggagalkan swap yang sudah sukses
            print(f"[WARN] gagal submit hash ke Textile: {exc}")

        # --- 6. Verifikasi tag di chain ---
        hashes = [h for h in (approval_hash, swap_hash, payout_hash) if h]
        verified = [verify_tx(w3, h, [code]) for h in hashes]
        for item in verified:
            print(f"[VERIFY] {item['tx_hash']} -> {item['codes']} ok={item['ok']}")

        return PaymentResult(
            quote=quote,
            approval_hash=approval_hash,
            swap_hash=swap_hash,
            payout_hash=payout_hash,
            verified=verified,
        )
