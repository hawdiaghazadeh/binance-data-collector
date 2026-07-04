"""Binance kline CSV parser plugin."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from quant_platform.core.plugin import PluginLifecycle, PluginMetadata
from services.importer.csv_parser import parse_zip_klines
from services.shared.validation import parse_csv_stream

PLUGIN_METADATA = PluginMetadata(
    name="binance_kline_csv",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    author="crypto-pipeline",
    description="Binance monthly kline CSV parser",
    lifecycle=PluginLifecycle.TRANSIENT,
    registry_group="platform.parsers",
)


class BinanceKlineParser:
    def parse_csv_stream(self, data: bytes, *, symbol: str, timeframe: str) -> Any:
        return parse_csv_stream(data, symbol=symbol, timeframe=timeframe)

    def parse_zip_klines(
        self,
        zip_path: Any,
        symbol: str,
        timeframe: str,
        *,
        validate_gaps: bool = True,
    ) -> Any:
        path = Path(zip_path) if not isinstance(zip_path, Path) else zip_path
        return parse_zip_klines(path, symbol, timeframe, validate_gaps=validate_gaps)


def factory(*, config: Any = None) -> BinanceKlineParser:
    return BinanceKlineParser()
