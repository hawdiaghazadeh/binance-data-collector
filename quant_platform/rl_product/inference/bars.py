"""Kline resolution for RL policy strategy (G37)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from quant_platform.core.context import PipelineContext
from services.shared.models import KlineRow


def _default_time(index: int) -> tuple[datetime, datetime]:
    base = datetime(2022, 1, 1, tzinfo=timezone.utc)
    open_time = base + timedelta(hours=index)
    return open_time, open_time + timedelta(hours=1)


def coerce_kline_row(row: object, *, index: int = 0, symbol: str = "BTCUSDT", timeframe: str = "1h") -> KlineRow:
    if isinstance(row, KlineRow):
        return row
    open_time, close_time = _default_time(index)
    if isinstance(row, dict):
        close = float(row.get("close", row.get("c", 0.0)))
        return KlineRow(
            symbol=str(row.get("symbol", symbol)),
            timeframe=str(row.get("timeframe", timeframe)),
            open_time=row.get("open_time", open_time),
            open=float(row.get("open", row.get("o", close))),
            high=float(row.get("high", row.get("h", close))),
            low=float(row.get("low", row.get("l", close))),
            close=close,
            volume=float(row.get("volume", row.get("v", 0.0))),
            close_time=row.get("close_time", close_time),
            quote_volume=float(row.get("quote_volume", close * 100)),
            trade_count=int(row.get("trade_count", 0)),
            taker_buy_volume=float(row.get("taker_buy_volume", 0.0)),
            taker_buy_quote_volume=float(row.get("taker_buy_quote_volume", 0.0)),
        )
    close = float(getattr(row, "close"))
    return KlineRow(
        symbol=str(getattr(row, "symbol", symbol)),
        timeframe=str(getattr(row, "timeframe", timeframe)),
        open_time=getattr(row, "open_time", open_time),
        open=float(getattr(row, "open", close)),
        high=float(getattr(row, "high", close)),
        low=float(getattr(row, "low", close)),
        close=close,
        volume=float(getattr(row, "volume", 0.0)),
        close_time=getattr(row, "close_time", close_time),
        quote_volume=float(getattr(row, "quote_volume", close * 100)),
        trade_count=int(getattr(row, "trade_count", 0)),
        taker_buy_volume=float(getattr(row, "taker_buy_volume", 0.0)),
        taker_buy_quote_volume=float(getattr(row, "taker_buy_quote_volume", 0.0)),
    )


def resolve_klines(ctx: PipelineContext, *, symbol: str = "BTCUSDT", timeframe: str = "1h") -> list[KlineRow]:
    envelope = ctx.require("klines")
    payload = envelope.payload
    if not isinstance(payload, list):
        raise TypeError("klines payload must be a list")
    return [
        coerce_kline_row(row, index=index, symbol=symbol, timeframe=timeframe)
        for index, row in enumerate(payload)
    ]
