"""Hybrid discrete + continuous action helpers (Phase 10)."""

from __future__ import annotations

import random
from typing import Any

from quant_platform.core.context import PipelineContext
from quant_platform.actions.continuous import sample_continuous_action
from quant_platform.actions.discrete import DEFAULT_DISCRETE_ACTIONS, sample_discrete_action


def sample_hybrid_action(
    ctx: PipelineContext,
    *,
    side_actions: tuple[str, ...] = ("hold", "buy", "sell"),
    size_low: float = 0.0,
    size_high: float = 1.0,
    exploration: float = 0.0,
    exploration_std: float = 0.0,
    rng: random.Random | None = None,
) -> dict[str, Any]:
    """Sample side from discrete space and magnitude from continuous space."""
    side = sample_discrete_action(ctx, actions=side_actions, exploration=exploration, rng=rng)
    if side == "hold":
        size = 0.0
    else:
        size = sample_continuous_action(
            ctx,
            low=size_low,
            high=size_high,
            exploration_std=exploration_std,
            rng=rng,
        )
        size = abs(size)
    return {"side": side, "size": size}


def apply_hybrid_action(ctx: PipelineContext, action: Any) -> None:
    from quant_platform.core.context import DataEnvelope

    if not isinstance(action, dict):
        raise TypeError("Hybrid action must be a dict with side and size")
    side = str(action.get("side", "hold"))
    size = float(action.get("size", 0.0))
    if side == "hold":
        size = 0.0
    ctx.emit(
        DataEnvelope(
            type_key="action",
            payload={"space": "hybrid", "side": side, "size": size},
        )
    )
