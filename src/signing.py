"""EIP-712 takerProof untuk Textile FX RFQ (jalur tanpa API key)."""
from __future__ import annotations

import secrets
import time

from eth_account import Account
from eth_account.messages import encode_typed_data


def sign_taker_control(private_key: str, chain_id: int, taker: str) -> dict:
    """Buat challenge pembuktian kepemilikan wallet.

    domain:  { name: "Textile Taker Control", version: "1", chainId }
    type:    TakerControl { taker, chainId, nonce, issuedAt }
    nonce  = 32 bytes acak, issuedAt = Unix milliseconds.
    """
    nonce = "0x" + secrets.token_hex(32)
    issued_at = int(time.time() * 1000)

    typed_data = {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
            ],
            "TakerControl": [
                {"name": "taker", "type": "address"},
                {"name": "chainId", "type": "uint256"},
                {"name": "nonce", "type": "bytes32"},
                {"name": "issuedAt", "type": "uint256"},
            ],
        },
        "primaryType": "TakerControl",
        "domain": {
            "name": "Textile Taker Control",
            "version": "1",
            "chainId": chain_id,
        },
        "message": {
            "taker": taker,
            "chainId": chain_id,
            "nonce": nonce,
            "issuedAt": issued_at,
        },
    }

    signable = encode_typed_data(full_message=typed_data)
    signature = Account.sign_message(signable, private_key).signature.hex()
    if not signature.startswith("0x"):
        signature = "0x" + signature

    return {"nonce": nonce, "issuedAt": issued_at, "signature": signature}
