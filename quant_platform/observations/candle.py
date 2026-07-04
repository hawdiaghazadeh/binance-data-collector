"""Candle window observation builder (Phase 8)."""

from __future__ import annotations

from quant_platform.market_structure.bars import Bar


def build_candle_observation(bars: list[Bar], *, window: int = 10) -> dict[str, object]:
    """Build normalized OHLC features for the most recent candle window."""
    if window < 1:
        raise ValueError("window must be >= 1")
    if not bars:
        return {"window": window, "features": [], "length": 0, "reference_close": 0.0}

    recent = bars[-window:]
    reference = recent[-1].close or 1.0
    features: list[list[float]] = []
    for bar in recent:
        features.append(
            [
                bar.open / reference - 1.0,
                bar.high / reference - 1.0,
                bar.low / reference - 1.0,
                bar.close / reference - 1.0,
            ]
        )

    padding = window - len(features)
    if padding > 0:
        features = [[0.0, 0.0, 0.0, 0.0] for _ in range(padding)] + features

    return {
        "window": window,
        "features": features,
        "length": len(recent),
        "reference_close": reference,
    }
