"""Market regime label computation (Phase 7)."""

from __future__ import annotations

import math


def compute_regime_labels(
    closes: list[float],
    *,
    window: int = 20,
    trend_threshold: float = 0.02,
    volatility_threshold: float = 0.01,
) -> list[str | None]:
    """Classify rolling market regime as trending, ranging, or high volatility."""
    if window < 2:
        raise ValueError("window must be >= 2")
    if not closes:
        return []

    labels: list[str | None] = [None] * len(closes)
    for index in range(window - 1, len(closes)):
        window_closes = closes[index - window + 1 : index + 1]
        start = window_closes[0]
        end = window_closes[-1]
        if start == 0:
            continue

        total_return = (end - start) / start
        mean = sum(window_closes) / len(window_closes)
        variance = sum((value - mean) ** 2 for value in window_closes) / len(window_closes)
        volatility = math.sqrt(variance) / mean if mean else 0.0

        if volatility >= volatility_threshold:
            labels[index] = "high_volatility"
        elif total_return >= trend_threshold:
            labels[index] = "trending_bull"
        elif total_return <= -trend_threshold:
            labels[index] = "trending_bear"
        else:
            labels[index] = "ranging"
    return labels
