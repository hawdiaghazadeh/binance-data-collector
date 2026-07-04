"""Binance REST API client (Phase 14)."""

from __future__ import annotations

from typing import Any, Protocol

import httpx


class HttpClient(Protocol):
    def get(self, url: str, *, params: dict[str, Any] | None = None) -> httpx.Response: ...


class BinanceRestClient:
    """USDT-M futures REST adapter for ticker and kline endpoints."""

    def __init__(
        self,
        *,
        base_url: str = "https://fapi.binance.com",
        client: httpx.Client | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = client or httpx.Client(timeout=timeout)
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def fetch_ticker_price(self, symbol: str) -> dict[str, Any]:
        response = self._client.get(
            f"{self._base_url}/fapi/v1/ticker/price",
            params={"symbol": symbol.upper()},
        )
        response.raise_for_status()
        payload = response.json()
        return {
            "symbol": payload["symbol"],
            "price": float(payload["price"]),
        }

    def fetch_klines_raw(
        self,
        symbol: str,
        interval: str,
        *,
        limit: int = 100,
    ) -> list[list[Any]]:
        response = self._client.get(
            f"{self._base_url}/fapi/v1/klines",
            params={
                "symbol": symbol.upper(),
                "interval": interval,
                "limit": limit,
            },
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            raise ValueError("Unexpected klines response")
        return payload
