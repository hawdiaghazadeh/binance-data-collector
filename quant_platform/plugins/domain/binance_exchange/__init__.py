"""Reference domain plugin: binance_exchange."""

from __future__ import annotations

from quant_platform.plugins.domain._helpers import attach_factory_metadata, reference_meta

PLUGIN_METADATA = reference_meta("binance_exchange", "platform.exchanges")


class BinanceExchange:

    def fetch_ticker(self, symbol: str) -> dict:
        return {"symbol": symbol, "price": 0.0}

    def fetch_ohlcv(self, symbol: str, timeframe: str) -> list:
        return []


def factory(**kwargs) -> BinanceExchange:
    return BinanceExchange()


attach_factory_metadata(factory, PLUGIN_METADATA)
