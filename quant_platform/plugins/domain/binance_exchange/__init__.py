"""Binance exchange plugin (Phase 14)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.plugin import PluginMetadata
from quant_platform.exchanges.binance import BinanceRestClient
from quant_platform.exchanges.parse import parse_binance_klines

PLUGIN_METADATA = PluginMetadata(
    name="binance_exchange",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Binance USDT-M futures REST adapter for ticker and OHLCV",
    input_types=["symbol", "timeframe"],
    output_types=["ticker", "klines", "price"],
    registry_group="platform.exchanges",
)


class BinanceExchange:
    def __init__(self, client: BinanceRestClient) -> None:
        self._client = client

    def fetch_ticker(self, symbol: str) -> dict[str, Any]:
        return self._client.fetch_ticker_price(symbol)

    def fetch_ohlcv(self, symbol: str, timeframe: str, *, limit: int = 100) -> list[Any]:
        raw = self._client.fetch_klines_raw(symbol, timeframe, limit=limit)
        return parse_binance_klines(raw, symbol=symbol, timeframe=timeframe)

    def fetch_ticker_to_context(self, ctx: PipelineContext, symbol: str) -> dict[str, Any]:
        ticker = self.fetch_ticker(symbol)
        ctx.emit(DataEnvelope(type_key="ticker", payload=ticker))
        ctx.emit(DataEnvelope(type_key="price", payload=ticker["price"]))
        return ticker


def factory(
    *,
    base_url: str = "https://fapi.binance.com",
    client: BinanceRestClient | None = None,
    config: dict | None = None,
    **kwargs,
) -> BinanceExchange:
    if config:
        base_url = str(config.get("base_url", base_url))
        client = config.get("client", client)
    if client is None:
        client = BinanceRestClient(base_url=base_url)
    return BinanceExchange(client)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
