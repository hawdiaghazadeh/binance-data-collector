"""UTC time range helpers for monthly kline files."""

from __future__ import annotations

from datetime import datetime, timezone


def month_range_utc(year: int, month: int) -> tuple[datetime, datetime]:
    """
    Return [start, end) UTC datetime bounds for a calendar month.

    Each monthly Binance ZIP file contains candles within exactly one month.
    """
    if not 1 <= month <= 12:
        raise ValueError(f"Invalid month: {month}")

    start = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, month + 1, 1, tzinfo=timezone.utc)

    return start, end
