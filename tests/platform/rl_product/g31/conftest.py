"""G31 perception test helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from services.shared.models import KlineRow


def kline(
    *,
    close: float,
    index: int = 0,
    high: float | None = None,
    low: float | None = None,
    open_: float | None = None,
) -> KlineRow:
    base = datetime(2022, 1, 1, tzinfo=timezone.utc)
    open_time = base + timedelta(hours=index)
    o = open_ if open_ is not None else close - 0.5
    h = high if high is not None else close + 1.0
    low_val = low if low is not None else close - 1.0
    return KlineRow(
        symbol="BTCUSDT",
        timeframe="1h",
        open_time=open_time,
        open=o,
        high=h,
        low=low_val,
        close=close,
        volume=100.0,
        close_time=open_time + timedelta(hours=1) - timedelta(seconds=1),
        quote_volume=close * 100.0,
        trade_count=10,
        taker_buy_volume=50.0,
        taker_buy_quote_volume=close * 50.0,
    )


def trending_bars(count: int, *, start: float = 100.0, step: float = 0.5) -> list[KlineRow]:
    return [kline(close=start + i * step, index=i) for i in range(count)]
