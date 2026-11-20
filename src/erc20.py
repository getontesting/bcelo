"""Utilitas ERC-20 minimal untuk alur pembayaran."""
from __future__ import annotations

from decimal import Decimal

from web3 import Web3
from eth_utils import to_checksum_address

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_spender", "type": "address"},
        ],
        "name": "allowance",
        "outputs": [{"name": "remaining", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [{"name": "success", "type": "bool"}],
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"},
        ],
        "name": "transfer",
        "outputs": [{"name": "success", "type": "bool"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
]


def contract(w3: Web3, token_address: str):
    return w3.eth.contract(address=to_checksum_address(token_address), abi=ERC20_ABI)


def allowance(w3: Web3, token: str, owner: str, spender: str) -> int:
    return contract(w3, token).functions.allowance(
        to_checksum_address(owner), to_checksum_address(spender)
    ).call()


def decimals(w3: Web3, token: str) -> int:
    return contract(w3, token).functions.decimals().call()


def encode_transfer(token: str, recipient: str, amount: int) -> str:
    return contract_for_encoding(token).encode_abi(
        "transfer", [to_checksum_address(recipient), int(amount)]
    )


def encode_approve(token: str, spender: str, amount: int) -> str:
    return contract_for_encoding(token).encode_abi(
        "approve", [to_checksum_address(spender), int(amount)]
    )


def contract_for_encoding(token: str):
    """Contract object tanpa provider — cukup untuk encode calldata."""
    return Web3().eth.contract(address=to_checksum_address(token), abi=ERC20_ABI)


def to_atomic(amount: str | int | Decimal, token_decimals: int) -> int:
    return int(Decimal(str(amount)) * (10**token_decimals))
