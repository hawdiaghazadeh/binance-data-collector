"""Binance response parsing (Phase 14)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from services.shared.models import KlineRow


def parse_binance_klines(
    raw: list[list[Any]],
    *,
    symbol: str,
    timeframe: str,
) -> list[KlineRow]:
    rows: list[KlineRow] = []
    for item in raw:
        open_time = datetime.fromtimestamp(item[0] / 1000, tz=timezone.utc)
        close_time = datetime.fromtimestamp(item[6] / 1000, tz=timezone.utc)
        rows.append(
            KlineRow(
                symbol=symbol.upper(),
                timeframe=timeframe,
                open_time=open_time,
                open=float(item[1]),
                high=float(item[2]),
                low=float(item[3]),
                close=float(item[4]),
                volume=float(item[5]),
                close_time=close_time,
                quote_volume=float(item[7]),
                trade_count=int(item[8]),
                taker_buy_volume=float(item[9]),
                taker_buy_quote_volume=float(item[10]),
            )
        )
    return rows
