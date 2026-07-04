"""Symbol and timeframe normalization utilities (Phase 4)."""

from __future__ import annotations

import re
from dataclasses import is_dataclass, replace
from typing import Any

TIMEFRAME_ALIASES: dict[str, str] = {
    "1min": "1m",
    "1m": "1m",
    "5min": "5m",
    "5m": "5m",
    "15min": "15m",
    "15m": "15m",
    "30min": "30m",
    "30m": "30m",
    "1h": "1h",
    "1hour": "1h",
    "60m": "1h",
    "60min": "1h",
    "4h": "4h",
    "4hour": "4h",
    "240m": "4h",
    "1d": "1d",
    "1day": "1d",
    "d": "1d",
    "1w": "1w",
    "1week": "1w",
    "w": "1w",
}


def normalize_symbol(symbol: str) -> str:
    """Canonical exchange symbol: uppercase, no separators."""
    cleaned = re.sub(r"[\s/_-]+", "", symbol.strip())
    return cleaned.upper()


def normalize_timeframe(timeframe: str) -> str:
    """Map common timeframe aliases to canonical Binance-style values."""
    key = timeframe.strip().lower()
    if key in TIMEFRAME_ALIASES:
        return TIMEFRAME_ALIASES[key]
    raise ValueError(f"Unsupported timeframe: {timeframe!r}")


def _normalize_row(row: Any) -> Any:
    if isinstance(row, dict):
        symbol = normalize_symbol(str(row.get("symbol", "")))
        timeframe = normalize_timeframe(str(row.get("timeframe", "")))
        return {**row, "symbol": symbol, "timeframe": timeframe}
    if is_dataclass(row):
        symbol = normalize_symbol(str(getattr(row, "symbol", "")))
        timeframe = normalize_timeframe(str(getattr(row, "timeframe", "")))
        return replace(row, symbol=symbol, timeframe=timeframe)
    raise TypeError(f"Unsupported row type for normalization: {type(row)!r}")


def normalize_kline_rows(rows: list[Any]) -> list[Any]:
    """Normalize symbol and timeframe on each kline row."""
    return [_normalize_row(row) for row in rows]
