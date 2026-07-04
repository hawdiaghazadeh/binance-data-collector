"""Perception hint utilities — bounded probabilistic outputs only."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Sequence

from quant_platform.market_structure.bars import Bar, to_bars
from services.shared.models import KlineRow

FORBIDDEN_METADATA_KEYS = frozenset(
    {"level", "price", "high", "low", "top", "bottom", "open", "close", "zone_price"}
)


def clamp01(value: float) -> float:
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return max(0.0, min(1.0, float(value)))


def visible_bars(bars: Sequence[KlineRow], t: int) -> list[KlineRow]:
    if t < 0 or t >= len(bars):
        raise ValueError("t out of range")
    return list(bars[: t + 1])


def to_market_bars(bars: Sequence[Any]) -> list[Bar]:
    return to_bars(list(bars))


def log_returns(closes: list[float]) -> list[float]:
    if len(closes) < 2:
        return []
    out: list[float] = []
    for i in range(1, len(closes)):
        prev = closes[i - 1]
        if prev <= 0:
            out.append(0.0)
        else:
            out.append(math.log(closes[i] / prev))
    return out


def realized_vol(closes: list[float], window: int = 20) -> float:
    rets = log_returns(closes)
    if len(rets) < 2:
        return 0.0
    sample = rets[-window:]
    mean = sum(sample) / len(sample)
    var = sum((r - mean) ** 2 for r in sample) / len(sample)
    return math.sqrt(var)


def range_position(bars: list[Bar], lookback: int = 20) -> float:
    if not bars:
        return 0.5
    window = bars[-lookback:]
    hi = max(b.high for b in window)
    lo = min(b.low for b in window)
    rng = hi - lo
    if rng <= 0:
        return 0.5
    return clamp01((bars[-1].close - lo) / rng)


def decay_from_event(age: int, half_life: float = 10.0) -> float:
    if age < 0:
        return 0.0
    return clamp01(math.exp(-age / half_life))


@dataclass(frozen=True, slots=True)
class HintEnvelope:
    """Probabilistic perception hint — no raw price levels in payload."""

    family: str
    name: str
    value: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise ValueError(f"hint {self.name} must be in [0, 1], got {self.value}")
        for key, raw in self.metadata.items():
            if key in FORBIDDEN_METADATA_KEYS:
                raise ValueError(f"hint metadata must not contain raw level key: {key}")
            if isinstance(raw, (int, float)) and abs(float(raw)) > 1000:
                raise ValueError(f"hint metadata looks like raw price: {key}={raw}")


def make_hint(family: str, name: str, value: float, **metadata: Any) -> HintEnvelope:
    return HintEnvelope(family=family, name=name, value=clamp01(value), metadata=dict(metadata))
