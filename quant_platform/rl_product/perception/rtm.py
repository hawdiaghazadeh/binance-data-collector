"""RTM (Read The Market) probabilistic hint detectors."""

from __future__ import annotations

from typing import Any, Sequence

from quant_platform.rl_product.perception._helpers import (
    clamp01,
    make_hint,
    realized_vol,
    to_market_bars,
)


def compute_sd_strength(bars: Sequence[Any], *, lookback: int = 20):
    mbars = to_market_bars(bars)
    if len(mbars) < 5:
        return make_hint("rtm", "sd_strength", 0.0)
    window = mbars[-lookback:]
    hi = max(b.high for b in window)
    lo = min(b.low for b in window)
    rng = hi - lo
    if rng <= 0:
        return make_hint("rtm", "sd_strength", 0.0)
    touches = 0
    for bar in window:
        near_high = (hi - bar.high) / rng < 0.05 or (hi - bar.close) / rng < 0.05
        near_low = (bar.low - lo) / rng < 0.05 or (bar.close - lo) / rng < 0.05
        if near_high or near_low:
            touches += 1
    return make_hint("rtm", "sd_strength", clamp01(touches / len(window)), touches=touches)


def compute_sweep_prob(bars: Sequence[Any], *, lookback: int = 10) -> HintEnvelope:
    mbars = to_market_bars(bars)
    if len(mbars) < lookback + 1:
        return make_hint("rtm", "sweep_p", 0.0)
    prior = mbars[-lookback - 1 : -1]
    last = mbars[-1]
    prior_high = max(b.high for b in prior)
    prior_low = min(b.low for b in prior)
    bull_sweep = last.high > prior_high and last.close < prior_high
    bear_sweep = last.low < prior_low and last.close > prior_low
    if bull_sweep or bear_sweep:
        return make_hint("rtm", "sweep_p", 1.0, sweep_type="bull" if bull_sweep else "bear")
    wick_up = (last.high - max(last.open, last.close)) / max(last.close, 1e-9)
    wick_down = (min(last.open, last.close) - last.low) / max(last.close, 1e-9)
    return make_hint("rtm", "sweep_p", clamp01(max(wick_up, wick_down) * 5.0))


def compute_compression_prob(bars: Sequence[Any], *, short: int = 5, long: int = 20) -> HintEnvelope:
    mbars = to_market_bars(bars)
    closes = [b.close for b in mbars]
    if len(closes) < long + 1:
        return make_hint("rtm", "compression_p", 0.0)
    vol_short = realized_vol(closes, window=short)
    vol_long = realized_vol(closes, window=long)
    if vol_long <= 0:
        return make_hint("rtm", "compression_p", 0.0)
    ratio = vol_short / vol_long
    return make_hint("rtm", "compression_p", clamp01(1.0 - ratio))


def compute_flip_prob(bars: Sequence[Any], *, lookback: int = 15) -> HintEnvelope:
    mbars = to_market_bars(bars)
    if len(mbars) < lookback + 1:
        return make_hint("rtm", "flip_p", 0.0)
    window = mbars[-lookback - 1 : -1]
    last = mbars[-1]
    prior_low = min(b.low for b in window)
    prior_high = max(b.high for b in window)
    bull_flip = last.low < prior_low and last.close > prior_low
    bear_flip = last.high > prior_high and last.close < prior_high
    if bull_flip or bear_flip:
        return make_hint("rtm", "flip_p", 1.0)
    return make_hint("rtm", "flip_p", 0.0)
