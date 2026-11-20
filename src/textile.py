"""Client untuk Textile FX RFQ API v2 (Celo mainnet)."""
from __future__ import annotations

from typing import Any

import httpx

from .signing import sign_taker_control


class TextileError(RuntimeError):
    pass


class TextileClient:
    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        timeout: float = 75.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        # Firm quote bisa menahan ~70s (reply budget + decimals preflight).
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "TextileClient":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _post(
        self, path: str, body: dict[str, Any], extra_headers: dict[str, str] | None = None
    ) -> httpx.Response:
        headers = self._headers()
        if extra_headers:
            headers.update(extra_headers)
        return self._client.post(
            f"{self.base_url}{path}", json=body, headers=headers
        )

    def health(self) -> httpx.Response:
        return self._client.get(f"{self.base_url}/health", timeout=10.0)

    def preview(self, body: dict[str, Any]) -> dict:
        res = self._post("/rfq/preview", body)
        res.raise_for_status()
        return res.json()["data"]

    def request_quote(
        self,
        *,
        chain_id: int,
        sell_token: str,
        buy_token: str,
        sell_amount: int,
        taker: str,
        private_key: str,
    ) -> dict:
        """Ambil firm quote. Jalur keyless otomatis menandatangani takerProof
        saat server meminta (401 proof_of_control_required)."""
        body: dict[str, Any] = {
            "chainId": chain_id,
            "sellToken": sell_token,
            "buyToken": buy_token,
            "sellAmount": str(sell_amount),
            "taker": taker,
        }

        res = self._post("/rfq/request", body)
        if res.status_code == 401:
            try:
                reason = res.json().get("error", {}).get("details", {}).get("reason")
            except ValueError:
                reason = None
            if reason == "proof_of_control_required":
                body["takerProof"] = sign_taker_control(private_key, chain_id, taker)
                res = self._post("/rfq/request", body)
            else:
                raise TextileError(f"401 dari Textile: {res.text[:300]}")

        if not res.is_success:
            raise TextileError(
                f"HTTP {res.status_code} dari /rfq/request: {res.text[:1000]}"
            )
        data = res.json().get("data", {})
        if data.get("status") == "no_quote":
            raise TextileError(
                f"no_quote ({data.get('reason')}). "
                f"availableSellAmount={data.get('availableSellAmount')}"
            )
        if data.get("status") != "quoted":
            raise TextileError(f"Status quote tidak terduga: {data.get('status')}")
        return data

    def submit(self, rfq_id: str, claim_token: str, tx_hash: str) -> dict:
        res = self._post(
            f"/rfq/{rfq_id}/submit",
            {"txHash": tx_hash},
            {"X-Rfq-Claim": claim_token},
        )
        res.raise_for_status()
        return res.json()["data"]

    def status(self, rfq_id: str, claim_token: str) -> dict:
        res = self._client.get(
            f"{self.base_url}/rfq/{rfq_id}",
            headers={"X-Rfq-Claim": claim_token},
        )
        res.raise_for_status()
        return res.json()["data"]
