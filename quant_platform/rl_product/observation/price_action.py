"""Price-action block — normalized OHLCV dynamics (backbone)."""

from __future__ import annotations

import math
from typing import Any, Sequence

from quant_platform.rl_product.perception._helpers import clamp01, log_returns, realized_vol, visible_bars
from services.shared.models import KlineRow

AGGREGATE_DIMS = 10


def _safe_norm(value: float, reference: float) -> float:
    if reference <= 0 or math.isnan(reference) or math.isinf(reference):
        return 0.0
    out = value / reference - 1.0
    if math.isnan(out) or math.isinf(out):
        return 0.0
    return max(-5.0, min(5.0, out))


def _bar_feature_count(price_dims: int) -> int:
    usable = max(price_dims - AGGREGATE_DIMS, 0)
    return max(usable // 5, 1)


def build_price_action_block(
    bars: Sequence[KlineRow],
    t: int,
    *,
    price_dims: int,
    window: int,
) -> list[float]:
    """Build normalized price-action features from bars[0:t+1] only."""
    if price_dims < 1:
        raise ValueError("price_dims must be >= 1")

    view = visible_bars(bars, t)
    if not view:
        return [0.0] * price_dims

    max_bars = min(window, _bar_feature_count(price_dims), len(view))
    recent = view[-max_bars:]
    reference = recent[-1].close if recent[-1].close > 0 else 1.0
    volumes = [b.volume for b in recent]
    mean_vol = sum(volumes) / len(volumes) if volumes else 1.0

    features: list[float] = []
    for bar in recent:
        features.extend(
            [
                _safe_norm(bar.open, reference),
                _safe_norm(bar.high, reference),
                _safe_norm(bar.low, reference),
                _safe_norm(bar.close, reference),
                _safe_norm(bar.volume, mean_vol) if mean_vol > 0 else 0.0,
            ]
        )

    closes = [b.close for b in view]
    rets = log_returns(closes)
    features.append(rets[-1] if rets else 0.0)
    features.append(sum(rets[-5:]) / len(rets[-5:]) if rets else 0.0)
    features.append(sum(rets[-20:]) / len(rets[-20:]) if rets else 0.0)
    features.append(realized_vol(closes, window=10))
    features.append(realized_vol(closes, window=20))
    last = view[-1]
    vol_ratio = last.volume / mean_vol if mean_vol > 0 else 1.0
    features.append(max(-5.0, min(5.0, vol_ratio - 1.0)))
    rng = last.high - last.low
    body = (last.close - last.open) / rng if rng > 0 else 0.0
    features.append(max(-1.0, min(1.0, body)))
    upper_wick = (last.high - max(last.open, last.close)) / rng if rng > 0 else 0.0
    lower_wick = (min(last.open, last.close) - last.low) / rng if rng > 0 else 0.0
    features.extend([upper_wick, lower_wick])

    while len(features) < price_dims:
        features.append(0.0)
    return features[:price_dims]
