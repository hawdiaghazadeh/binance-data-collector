"""Direction label computation (Phase 7)."""

from __future__ import annotations


def compute_direction_labels(
    closes: list[float],
    *,
    horizon: int = 1,
    threshold_pct: float = 0.0,
) -> list[str | None]:
    """Label each bar by future price direction over the given horizon."""
    if horizon < 1:
        raise ValueError("horizon must be >= 1")
    if not closes:
        return []

    labels: list[str | None] = [None] * len(closes)
    for index in range(len(closes) - horizon):
        current = closes[index]
        future = closes[index + horizon]
        if current == 0:
            labels[index] = "neutral"
            continue
        change = (future - current) / current
        if change > threshold_pct:
            labels[index] = "bullish"
        elif change < -threshold_pct:
            labels[index] = "bearish"
        else:
            labels[index] = "neutral"
    return labels
