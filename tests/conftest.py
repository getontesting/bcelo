"""Isolasi test dari lingkungan Reviewer/CI.

Reviewer AskBots menjalankan test dalam container tanpa .env, tanpa secret,
dan tanpa akses jaringan. Kita hapus variabel sensitif dari os.environ untuk
setiap test supaya tidak ada test yang diam-diam bergantung pada kredensial
atau RPC lokal, lalu kembalikan setelahnya.
"""
from __future__ import annotations

import os

import pytest

_SENSITIVE = (
    "TAKER_PRIVATE_KEY",
    "PAYOUT_ADDRESS",
    "ATTRIBUTION_CODE",
    "RECIPIENT_ADDRESS",
    "AGENTVAULT_API_KEY",
    "X402_API_KEY",
    "ALTANA_ADMIN_PRIVATE_KEY",
    "BUYER_PRIVATE_KEY",
    "SELLER_PAY_TO",
)


@pytest.fixture(autouse=True)
def _isolate_environment(monkeypatch):
    for key in _SENSITIVE:
        monkeypatch.delenv(key, raising=False)
    # Jangan biarkan dotenv from .env lokal menyuntik nilai ke test.
    monkeypatch.setenv("PYTEST_CURRENT_TEST_OFFLINE", "1")
    yield
