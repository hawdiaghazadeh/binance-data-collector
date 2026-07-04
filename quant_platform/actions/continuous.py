"""Continuous action space helpers (Phase 10)."""

from __future__ import annotations

import random
from typing import Any

from quant_platform.core.context import PipelineContext


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))


def sample_continuous_action(
    ctx: PipelineContext,
    *,
    low: float = -1.0,
    high: float = 1.0,
    exploration_std: float = 0.0,
    rng: random.Random | None = None,
) -> float:
    """Sample a continuous position target in [low, high]."""
    if low >= high:
        raise ValueError("low must be less than high")
    if exploration_std < 0:
        raise ValueError("exploration_std must be >= 0")

    randomizer = rng or random.Random()
    policy_env = ctx.optional("policy_mean")
    if policy_env is not None:
        value = float(policy_env.payload)
    else:
        override_env = ctx.optional("action_override")
        value = float(override_env.payload) if override_env is not None else 0.0

    if exploration_std > 0:
        value += randomizer.gauss(0.0, exploration_std)

    return _clamp(value, low, high)


def apply_continuous_action(ctx: PipelineContext, action: Any, *, low: float, high: float) -> None:
    from quant_platform.core.context import DataEnvelope

    value = _clamp(float(action), low, high)
    ctx.emit(
        DataEnvelope(
            type_key="action",
            payload={"space": "continuous", "value": value, "low": low, "high": high},
        )
    )
