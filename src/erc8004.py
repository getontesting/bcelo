"""Registrasi identitas ERC-8004 di Celo mainnet (wajib semua track)."""
from __future__ import annotations

import base64
import json
from typing import Any

from eth_utils import to_checksum_address
from web3 import Web3

from .agent import send_tagged
from .attribution import append_tag

IDENTITY_REGISTRY = "0x8004A169FB4a3325136EB29fA0ceB6D2e539a432"

ABI: list[dict[str, Any]] = [
    {
        "type": "function",
        "name": "register",
        "stateMutability": "nonpayable",
        "inputs": [{"name": "agentURI", "type": "string"}],
        "outputs": [{"name": "agentId", "type": "uint256"}],
    },
    {
        "type": "function",
        "name": "setAgentURI",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "agentId", "type": "uint256"},
            {"name": "uri", "type": "string"},
        ],
        "outputs": [],
    },
    {
        "type": "function",
        "name": "balanceOf",
        "stateMutability": "view",
        "inputs": [{"name": "owner", "type": "address"}],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "type": "function",
        "name": "tokenOfOwnerByIndex",
        "stateMutability": "view",
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "index", "type": "uint256"},
        ],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "type": "event",
        "name": "Registered",
        "anonymous": False,
        "inputs": [
            {
                "name": "agentId",
                "type": "uint256",
                "indexed": True,
            },
            {"name": "agentURI", "type": "string", "indexed": False},
            {"name": "owner", "type": "address", "indexed": True},
        ],
    },
]


def build_registration(
    *,
    name: str,
    description: str,
    endpoint: str,
    x402_support: bool = True,
    agent_id: int | None = None,
) -> dict:
    """Buat file registration JSON sesuai ERC-8004 registration-v1."""
    doc: dict[str, Any] = {
        "type": "https://eips.ethereum.org/EIPS/eip-8004#registration-v1",
        "name": name,
        "description": description,
        "services": [{"name": "web", "endpoint": endpoint}],
        "x402Support": x402_support,
        "active": True,
        "supportedTrust": ["reputation"],
    }
    if agent_id is not None:
        doc["registrations"] = [
            {
                "agentId": agent_id,
                "agentRegistry": f"eip155:42220:{IDENTITY_REGISTRY}",
            }
        ]
    return doc


def to_data_uri(doc: dict) -> str:
    """Simpan registration file di calldata — tidak perlu hosting."""
    raw = json.dumps(doc, separators=(",", ":")).encode("utf-8")
    return "data:application/json;base64," + base64.b64encode(raw).decode("ascii")


def _contract(w3: Web3):
    return w3.eth.contract(address=to_checksum_address(IDENTITY_REGISTRY), abi=ABI)


def agent_id_for_owner(w3: Web3, owner: str) -> int | None:
    c = _contract(w3)
    count = c.functions.balanceOf(to_checksum_address(owner)).call()
    if count == 0:
        return None
    return int(c.functions.tokenOfOwnerByIndex(to_checksum_address(owner), 0).call())


def register(
    w3: Web3,
    private_key: str,
    agent_uri: str,
    attribution_code: str,
) -> int:
    """Mint NFT identitas. agentWallet = alamat yang menandatangani tx ini."""
    c = _contract(w3)
    data = append_tag(
        c.encode_abi("register", [agent_uri]), [attribution_code]
    )
    tx_hash = send_tagged(
        w3, private_key, to=IDENTITY_REGISTRY, data=data
    )
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    if receipt["status"] != 1:
        raise RuntimeError(f"Registrasi ERC-8004 gagal: {tx_hash}")
    events = c.events.Registered().process_receipt(receipt)
    if not events:
        raise RuntimeError(f"Event Registered tidak ditemukan di {tx_hash}")
    return int(events[0]["args"]["agentId"])


def set_agent_uri(
    w3: Web3,
    private_key: str,
    agent_id: int,
    agent_uri: str,
    attribution_code: str,
) -> str:
    """Update agentURI, misal setelah menambahkan `registrations`."""
    c = _contract(w3)
    data = append_tag(
        c.encode_abi("setAgentURI", [agent_id, agent_uri]), [attribution_code]
    )
    return send_tagged(w3, private_key, to=IDENTITY_REGISTRY, data=data)
