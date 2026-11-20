"""ERC-8021 attribution tag — implementasi murni Python.

Wire format (Schema 0 / app-emitted):
    [...calldata...] [code:N] [length:1] [schema:0x00] [marker:16]

Marker = 0x80218021 diulang 8x. Tag dibuang EVM saat eksekusi, jadi aman
ditaruh di akhir calldata. Sumber: github.com/celo-org/attribution-tags.
"""
from __future__ import annotations

import hashlib
import re

from web3 import Web3

MARKER_HEX = "80218021802180218021802180218021"
MARKER = bytes.fromhex(MARKER_HEX)
SCHEMA_APP = 0
SCHEMA_ROLE = 2

_CODE_RE = re.compile(r"^[a-z0-9_]{1,32}$")


def strip_0x(value: str) -> str:
    return value[2:] if value.lower().startswith("0x") else value


def normalize_codes(codes: list[str] | tuple[str, ...]) -> list[str]:
    """Validasi + dedupe code, urutan tetap dipertahankan."""
    out: list[str] = []
    for code in codes:
        if not isinstance(code, str) or not _CODE_RE.fullmatch(code):
            raise ValueError(
                f"Code attribution tidak valid: {code!r} "
                "(harus 1-32 karakter [a-z0-9_])"
            )
        if code not in out:
            out.append(code)
    if not out:
        raise ValueError("Minimal satu attribution code dibutuhkan")
    return out


def code_from_repo(repo: str) -> str:
    """Reproduksi codeFromRepo dari SDK Celo.

    Platform hackathon sering meng-assign code berdasarkan slug GitHub.
    """
    slug = repo.strip().lower()
    if slug.startswith("https://github.com/"):
        slug = slug[len("https://github.com/") :]
    slug = slug.strip("/")
    return "celo_" + hashlib.sha256(slug.encode()).hexdigest()[:12]


def code_from_hostname(hostname: str) -> str:
    """Reproduksi codeFromHostname (MiniPay-style, untuk perbandingan)."""
    host = hostname.strip().lower()
    if host.startswith("www."):
        host = host[4:]
    return "celo_" + hashlib.sha256(host.encode()).hexdigest()[:12]


def build_data_suffix(codes: list[str] | tuple[str, ...]) -> bytes:
    field = ",".join(normalize_codes(codes)).encode("ascii")
    if len(field) > 255:
        raise ValueError("Gabungan code terlalu panjang (maks 255 byte)")
    return field + bytes([len(field), SCHEMA_APP]) + MARKER


def parse_suffix(input_bytes: bytes) -> dict | None:
    """Decode tag dari akhir calldata. Mengikuti INDEXERS.md."""
    if len(input_bytes) < 19 or input_bytes[-16:] != MARKER:
        return None
    schema = input_bytes[-17]
    if schema == SCHEMA_APP:
        code_len = input_bytes[-18]
        if code_len == 0 or len(input_bytes) < 18 + code_len:
            return None
        field = input_bytes[-18 - code_len : -18].decode("ascii")
        return {"codes": field.split(","), "schema_id": schema}
    if schema == SCHEMA_ROLE:
        return None  # Schema 2 (facilitator) tidak kita tangani di sisi app.
    return None


def append_tag(calldata_hex: str, codes: list[str] | tuple[str, ...]) -> str:
    """Tempel tag di akhir calldata.

    Kalau calldata sudah punya Schema 0 tag (misal dari Textile
    includeAttribution), tag lama dilepas dan di-merge dengan code kita —
    JANGAN menambah suffix kedua, karena indexer hanya membaca yang terakhir.
    """
    data = bytes.fromhex(strip_0x(calldata_hex))
    existing = parse_suffix(data)
    merged: list[str] = []
    if existing is not None:
        if existing["schema_id"] != SCHEMA_APP:
            raise ValueError(
                "Calldata sudah punya Schema 2 tag dari facilitator; "
                "tidak bisa digabung dengan app tag."
            )
        code_len = data[-18]
        data = data[: -(code_len + 18)]
        merged.extend(existing["codes"])
    merged.extend(normalize_codes(codes))
    return "0x" + (data + build_data_suffix(merged)).hex()


def verify_tx(w3: Web3, tx_hash: str, expected_codes: list[str]) -> dict:
    """Cek di chain apakah transaksi benar-benar membawa code yang diharapkan."""
    tx = w3.eth.get_transaction(tx_hash)
    parsed = parse_suffix(bytes.fromhex(strip_0x(tx["input"])))
    if parsed is None:
        raise RuntimeError(f"Transaksi {tx_hash} TIDAK bertag / gagal di-decode")
    missing = [c for c in expected_codes if c not in parsed["codes"]]
    return {
        "tx_hash": tx_hash,
        "codes": parsed["codes"],
        "schema_id": parsed["schema_id"],
        "ok": not missing,
        "missing": missing,
    }
