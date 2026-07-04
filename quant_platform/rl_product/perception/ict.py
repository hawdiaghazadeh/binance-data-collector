"""ICT probabilistic hint detectors."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Sequence

from quant_platform.rl_product.perception._helpers import clamp01, make_hint, range_position, to_market_bars


def _bar_time(bars: Sequence[Any]) -> datetime | None:
    last = bars[-1]
    ts = getattr(last, "open_time", None)
    if ts is None and isinstance(last, dict):
        ts = last.get("open_time")
    if ts is None:
        return None
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc)
    return None


def compute_session_prob(bars: Sequence[Any]) -> HintEnvelope:
    ts = _bar_time(bars)
    if ts is None:
        return make_hint("ict", "session_p", 0.0)
    hour = ts.hour
    if 0 <= hour < 8:
        weight = 1.0 if hour < 4 else 0.6
        session = "asia"
    elif 7 <= hour < 16:
        weight = 1.0 if 8 <= hour < 12 else 0.7
        session = "london"
    else:
        weight = 1.0 if 13 <= hour < 17 else 0.65
        session = "ny"
    return make_hint("ict", "session_p", clamp01(weight), session=session)


def compute_killzone_prob(bars: Sequence[Any]) -> HintEnvelope:
    ts = _bar_time(bars)
    if ts is None:
        return make_hint("ict", "killzone_p", 0.0)
    hour = ts.hour + ts.minute / 60.0
    london_kz = 7.0 <= hour <= 10.0
    ny_am_kz = 12.0 <= hour <= 15.0
    ny_pm_kz = 18.0 <= hour <= 20.0
    if london_kz or ny_am_kz:
        return make_hint("ict", "killzone_p", 1.0)
    if ny_pm_kz:
        return make_hint("ict", "killzone_p", 0.6)
    return make_hint("ict", "killzone_p", 0.0)


def compute_premium_discount(bars: Sequence[Any], *, lookback: int = 20) -> HintEnvelope:
    mbars = to_market_bars(bars)
    pos = range_position(mbars, lookback=lookback)
    return make_hint("ict", "premium_discount", pos)
