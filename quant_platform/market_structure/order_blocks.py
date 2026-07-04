"""Order block detection (Phase 6)."""

from __future__ import annotations

from typing import Any

from quant_platform.market_structure.bars import Bar


def _is_bullish(bar: Bar) -> bool:
    return bar.close > bar.open


def _is_bearish(bar: Bar) -> bool:
    return bar.close < bar.open


def detect_order_blocks(bars: list[Bar], displacement_pct: float = 0.005) -> list[dict[str, Any]]:
    if displacement_pct <= 0:
        raise ValueError("displacement_pct must be > 0")

    blocks: list[dict[str, Any]] = []
    seen: set[int] = set()

    for index in range(1, len(bars)):
        previous = bars[index - 1]
        current = bars[index]
        if previous.close == 0:
            continue

        change = (current.close - previous.close) / previous.close
        if change >= displacement_pct:
            for candidate in range(index - 1, -1, -1):
                if _is_bearish(bars[candidate]) and candidate not in seen:
                    blocks.append(
                        {
                            "index": candidate,
                            "direction": "bullish",
                            "high": bars[candidate].high,
                            "low": bars[candidate].low,
                            "displacement_index": index,
                            "displacement_pct": change,
                        }
                    )
                    seen.add(candidate)
                    break
        elif change <= -displacement_pct:
            for candidate in range(index - 1, -1, -1):
                if _is_bullish(bars[candidate]) and candidate not in seen:
                    blocks.append(
                        {
                            "index": candidate,
                            "direction": "bearish",
                            "high": bars[candidate].high,
                            "low": bars[candidate].low,
                            "displacement_index": index,
                            "displacement_pct": change,
                        }
                    )
                    seen.add(candidate)
                    break

    return blocks
