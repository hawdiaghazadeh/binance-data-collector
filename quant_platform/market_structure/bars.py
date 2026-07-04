"""OHLC bar helpers for market structure analysis (Phase 6)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Bar:
    open: float
    high: float
    low: float
    close: float
    index: int = 0


def row_field(row: object, field: str) -> float:
    if hasattr(row, field):
        return float(getattr(row, field))
    if isinstance(row, dict):
        return float(row[field])
    raise TypeError(f"Unsupported row type: {type(row)!r}")


def to_bars(rows: list[Any]) -> list[Bar]:
    bars: list[Bar] = []
    for index, row in enumerate(rows):
        bars.append(
            Bar(
                open=row_field(row, "open"),
                high=row_field(row, "high"),
                low=row_field(row, "low"),
                close=row_field(row, "close"),
                index=index,
            )
        )
    return bars
