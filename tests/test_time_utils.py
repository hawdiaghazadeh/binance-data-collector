"""Tests for time utilities."""

from datetime import datetime, timezone

from services.shared.time_utils import month_range_utc


def test_month_range_utc_january() -> None:
    start, end = month_range_utc(2024, 1)
    assert start == datetime(2024, 1, 1, tzinfo=timezone.utc)
    assert end == datetime(2024, 2, 1, tzinfo=timezone.utc)


def test_month_range_utc_december() -> None:
    start, end = month_range_utc(2024, 12)
    assert start == datetime(2024, 12, 1, tzinfo=timezone.utc)
    assert end == datetime(2025, 1, 1, tzinfo=timezone.utc)
