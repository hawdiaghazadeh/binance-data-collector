"""Perception compressor — hint envelopes to fixed context vector."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Sequence

from quant_platform.rl_product.perception._helpers import clamp01, log_returns, realized_vol, to_market_bars

SLOT_NAMES_16: list[str] = [
    "bos_p",
    "choch_p",
    "ob_validity",
    "fvg_fill_p",
    "sd_strength",
    "sweep_p",
    "compression_p",
    "flip_p",
    "session_p",
    "killzone_p",
    "premium_discount",
    "tod_norm",
    "regime_vol",
    "trend_persist",
    "hint_entropy",
    "gate_mask",
]

SLOT_FAMILIES: dict[str, str] = {
    "bos_p": "smc",
    "choch_p": "smc",
    "ob_validity": "smc",
    "fvg_fill_p": "smc",
    "sd_strength": "rtm",
    "sweep_p": "rtm",
    "compression_p": "rtm",
    "flip_p": "rtm",
    "session_p": "ict",
    "killzone_p": "ict",
    "premium_discount": "ict",
    "tod_norm": "ict",
    "regime_vol": "meta",
    "trend_persist": "meta",
    "hint_entropy": "meta",
    "gate_mask": "meta",
}

CONTEXT_DIMS_MIN = 16
CONTEXT_DIMS_MAX = 32


class PerceptionCompressor:
    """Merge hint values and meta features into a bounded context vector."""

    __slots__ = ("context_dims",)

    def __init__(self, *, context_dims: int = 16) -> None:
        if context_dims < CONTEXT_DIMS_MIN or context_dims > CONTEXT_DIMS_MAX:
            raise ValueError(f"context_dims must be in [{CONTEXT_DIMS_MIN}, {CONTEXT_DIMS_MAX}]")
        self.context_dims = context_dims

    def slot_names(self) -> list[str]:
        if self.context_dims <= 16:
            return SLOT_NAMES_16[: self.context_dims]
        extra = [f"reserved_{i}" for i in range(16, self.context_dims)]
        return SLOT_NAMES_16 + extra

    def compress(self, bars: Sequence[Any], hints: dict[str, float]) -> list[float]:
        vec = [0.0] * self.context_dims
        names = self.slot_names()
        mbars = to_market_bars(bars) if bars else []

        for i, name in enumerate(names):
            if name.startswith("reserved_"):
                vec[i] = 0.0
                continue
            if name == "tod_norm":
                vec[i] = self._tod_norm(bars)
            elif name == "regime_vol":
                closes = [b.close for b in mbars]
                vec[i] = clamp01(realized_vol(closes, window=20) * 50.0)
            elif name == "trend_persist":
                vec[i] = self._trend_persist(mbars)
            elif name == "hint_entropy":
                vec[i] = self._hint_entropy(hints)
            elif name == "gate_mask":
                vec[i] = 1.0
            else:
                vec[i] = clamp01(hints.get(name, 0.0))
        return vec

    def _tod_norm(self, bars: Sequence[Any]) -> float:
        if not bars:
            return 0.0
        last = bars[-1]
        ts = getattr(last, "open_time", None)
        if ts is None and isinstance(last, dict):
            ts = last.get("open_time")
        if not isinstance(ts, datetime):
            return 0.0
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        minutes = ts.hour * 60 + ts.minute
        return clamp01(minutes / (24 * 60))

    def _trend_persist(self, bars: list) -> float:
        if len(bars) < 4:
            return 0.0
        closes = [b.close for b in bars]
        rets = log_returns(closes)
        if len(rets) < 2:
            return 0.0
        signs = [1 if r > 0 else (-1 if r < 0 else 0) for r in rets[-10:]]
        if not signs:
            return 0.0
        same = sum(1 for i in range(1, len(signs)) if signs[i] == signs[i - 1] and signs[i] != 0)
        return clamp01(same / max(len(signs) - 1, 1))

    def _hint_entropy(self, hints: dict[str, float]) -> float:
        values = [clamp01(v) for v in hints.values() if v > 0]
        if not values:
            return 0.0
        total = sum(values)
        if total <= 0:
            return 0.0
        probs = [v / total for v in values]
        entropy = -sum(p * math.log(p + 1e-12) for p in probs)
        max_entropy = math.log(len(probs) + 1e-12)
        if max_entropy <= 0:
            return 0.0
        return clamp01(entropy / max_entropy)
