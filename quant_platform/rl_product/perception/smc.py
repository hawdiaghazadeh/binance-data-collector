"""SMC probabilistic hint detectors."""

from __future__ import annotations

from typing import Any, Sequence

from quant_platform.market_structure.bos_choch import detect_bos_choch
from quant_platform.market_structure.fvg import detect_fvg
from quant_platform.market_structure.order_blocks import detect_order_blocks
from quant_platform.rl_product.perception._helpers import (
    HintEnvelope,
    clamp01,
    decay_from_event,
    make_hint,
    to_market_bars,
)


def compute_bos_prob(bars: Sequence[Any], *, swing_lookback: int = 2) -> HintEnvelope:
    mbars = to_market_bars(bars)
    if len(mbars) < 3:
        return make_hint("smc", "bos_p", 0.0)
    bos, _ = detect_bos_choch(mbars, swing_lookback=swing_lookback)
    if not bos:
        return make_hint("smc", "bos_p", 0.0)
    age = len(mbars) - 1 - bos[-1]["index"]
    return make_hint("smc", "bos_p", decay_from_event(age), event_age=age)


def compute_choch_prob(bars: Sequence[Any], *, swing_lookback: int = 2) -> HintEnvelope:
    mbars = to_market_bars(bars)
    if len(mbars) < 3:
        return make_hint("smc", "choch_p", 0.0)
    _, choch = detect_bos_choch(mbars, swing_lookback=swing_lookback)
    if not choch:
        return make_hint("smc", "choch_p", 0.0)
    age = len(mbars) - 1 - choch[-1]["index"]
    return make_hint("smc", "choch_p", decay_from_event(age), event_age=age)


def compute_ob_validity(bars: Sequence[Any], *, displacement_pct: float = 0.005) -> HintEnvelope:
    mbars = to_market_bars(bars)
    if len(mbars) < 5:
        return make_hint("smc", "ob_validity", 0.0)
    blocks = detect_order_blocks(mbars, displacement_pct=displacement_pct)
    if not blocks:
        return make_hint("smc", "ob_validity", 0.0)
    close = mbars[-1].close
    window = mbars[-min(20, len(mbars)) :]
    hi = max(b.high for b in window)
    lo = min(b.low for b in window)
    rng = hi - lo
    if rng <= 0:
        return make_hint("smc", "ob_validity", 0.0)
    best = 0.0
    for block in blocks:
        mid = (block["high"] + block["low"]) / 2.0
        dist = abs(close - mid) / rng
        best = max(best, clamp01(1.0 - dist * 2.0))
    return make_hint("smc", "ob_validity", best, block_count=len(blocks))


def compute_fvg_fill_prob(bars: Sequence[Any]) -> HintEnvelope:
    mbars = to_market_bars(bars)
    if len(mbars) < 3:
        return make_hint("smc", "fvg_fill_p", 0.0)
    gaps = detect_fvg(mbars)
    if not gaps:
        return make_hint("smc", "fvg_fill_p", 0.0)
    last = gaps[-1]
    close = mbars[-1].close
    top = last["top"]
    bottom = last["bottom"]
    size = top - bottom
    if size <= 0:
        return make_hint("smc", "fvg_fill_p", 0.0)
    if last["direction"] == "bullish":
        fill = clamp01((top - close) / size)
    else:
        fill = clamp01((close - bottom) / size)
    return make_hint("smc", "fvg_fill_p", fill, direction=last["direction"])
