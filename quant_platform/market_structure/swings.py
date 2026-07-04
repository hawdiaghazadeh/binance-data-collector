"""Swing point detection (Phase 6)."""

from __future__ import annotations

from dataclasses import dataclass

from quant_platform.market_structure.bars import Bar


@dataclass(frozen=True)
class SwingPoint:
    index: int
    price: float
    kind: str


def find_swings(bars: list[Bar], lookback: int = 2) -> list[SwingPoint]:
    if lookback < 1:
        raise ValueError("lookback must be >= 1")
    if len(bars) < lookback * 2 + 1:
        return []

    swings: list[SwingPoint] = []
    for index in range(lookback, len(bars) - lookback):
        window = bars[index - lookback : index + lookback + 1]
        highs = [bar.high for bar in window]
        lows = [bar.low for bar in window]
        if bars[index].high == max(highs):
            swings.append(SwingPoint(index=index, price=bars[index].high, kind="high"))
        if bars[index].low == min(lows):
            swings.append(SwingPoint(index=index, price=bars[index].low, kind="low"))
    return swings
