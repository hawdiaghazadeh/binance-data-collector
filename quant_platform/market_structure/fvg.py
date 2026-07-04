"""Fair Value Gap detection (Phase 6)."""

from __future__ import annotations

from typing import Any

from quant_platform.market_structure.bars import Bar


def detect_fvg(bars: list[Bar]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for index in range(2, len(bars)):
        first = bars[index - 2]
        third = bars[index]
        if third.low > first.high:
            gaps.append(
                {
                    "index": index,
                    "direction": "bullish",
                    "top": third.low,
                    "bottom": first.high,
                    "size": third.low - first.high,
                }
            )
        elif third.high < first.low:
            gaps.append(
                {
                    "index": index,
                    "direction": "bearish",
                    "top": first.low,
                    "bottom": third.high,
                    "size": first.low - third.high,
                }
            )
    return gaps
