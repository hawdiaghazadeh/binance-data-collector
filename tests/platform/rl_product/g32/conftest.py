"""G32 observation test helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from services.shared.models import KlineRow


def kline(*, close: float, index: int = 0, volume: float = 100.0) -> KlineRow:
    base = datetime(2022, 1, 1, tzinfo=timezone.utc)
    open_time = base + timedelta(hours=index)
    return KlineRow(
        symbol="BTCUSDT",
        timeframe="1h",
        open_time=open_time,
        open=close - 0.5,
        high=close + 1.0,
        low=close - 1.0,
        close=close,
        volume=volume,
        close_time=open_time + timedelta(hours=1) - timedelta(seconds=1),
        quote_volume=close * volume,
        trade_count=10,
        taker_buy_volume=volume / 2,
        taker_buy_quote_volume=close * volume / 2,
    )


def trending_bars(count: int) -> list[KlineRow]:
    return [kline(close=100.0 + i * 0.3, index=i, volume=100.0 + i) for i in range(count)]
