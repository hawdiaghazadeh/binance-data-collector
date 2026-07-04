"""Break of Structure and Change of Character detection (Phase 6)."""

from __future__ import annotations

from typing import Any

from quant_platform.market_structure.bars import Bar
from quant_platform.market_structure.swings import SwingPoint, find_swings


def detect_bos_choch(bars: list[Bar], swing_lookback: int = 2) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    swings = find_swings(bars, swing_lookback)
    if not swings:
        return [], []

    bos: list[dict[str, Any]] = []
    choch: list[dict[str, Any]] = []
    trend: str | None = None
    active_high: SwingPoint | None = None
    active_low: SwingPoint | None = None
    swing_at_index = {swing.index: swing for swing in swings}
    triggered: set[tuple[str, int]] = set()

    for index in range(len(bars)):
        if index in swing_at_index:
            swing = swing_at_index[index]
            if swing.kind == "high":
                active_high = swing
            else:
                active_low = swing

        if active_high is None or active_low is None:
            continue

        close = bars[index].close
        bullish_key = ("bullish", active_high.index)
        if (
            close > active_high.price
            and index > active_high.index
            and bullish_key not in triggered
        ):
            event = {
                "index": index,
                "kind": "bullish_choch" if trend == "bearish" else "bullish_bos",
                "level": active_high.price,
                "swing_index": active_high.index,
            }
            if trend == "bearish":
                choch.append(event)
            else:
                bos.append(event)
            trend = "bullish"
            triggered.add(bullish_key)

        bearish_key = ("bearish", active_low.index)
        if (
            close < active_low.price
            and index > active_low.index
            and bearish_key not in triggered
        ):
            event = {
                "index": index,
                "kind": "bearish_choch" if trend == "bullish" else "bearish_bos",
                "level": active_low.price,
                "swing_index": active_low.index,
            }
            if trend == "bullish":
                choch.append(event)
            else:
                bos.append(event)
            trend = "bearish"
            triggered.add(bearish_key)

    return bos, choch
