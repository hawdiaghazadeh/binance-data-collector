"""Discrete action space helpers (Phase 10)."""

from __future__ import annotations

import random
from typing import Any

from quant_platform.core.context import PipelineContext

DEFAULT_DISCRETE_ACTIONS = ("hold", "buy", "sell")


def resolve_policy_probs(ctx: PipelineContext, actions: tuple[str, ...]) -> list[float] | None:
    policy_env = ctx.optional("policy_probs")
    if policy_env is None:
        return None
    probs = [float(value) for value in policy_env.payload]
    if len(probs) != len(actions):
        raise ValueError("policy_probs length must match action space")
    return probs


def resolve_signal_action(ctx: PipelineContext) -> str | None:
    signals_env = ctx.optional("strategy_signals")
    if signals_env is None:
        return None
    signals = signals_env.payload
    if not isinstance(signals, list) or not signals:
        return None
    latest = signals[-1]
    if isinstance(latest, dict):
        side = str(latest.get("side", "")).lower()
        if side in DEFAULT_DISCRETE_ACTIONS:
            return side
        if side in {"long", "short"}:
            return "buy" if side == "long" else "sell"
    return None


def sample_discrete_action(
    ctx: PipelineContext,
    *,
    actions: tuple[str, ...] = DEFAULT_DISCRETE_ACTIONS,
    exploration: float = 0.0,
    rng: random.Random | None = None,
) -> str:
    """Sample a discrete action from policy probabilities, strategy signals, or exploration."""
    if exploration < 0 or exploration > 1:
        raise ValueError("exploration must be between 0 and 1")

    randomizer = rng or random.Random()
    if exploration > 0 and randomizer.random() < exploration:
        return randomizer.choice(list(actions))

    probs = resolve_policy_probs(ctx, actions)
    if probs is not None:
        threshold = randomizer.random()
        cumulative = 0.0
        for action, prob in zip(actions, probs, strict=True):
            cumulative += prob
            if threshold <= cumulative:
                return action
        return actions[-1]

    signal_action = resolve_signal_action(ctx)
    if signal_action is not None:
        return signal_action

    override_env = ctx.optional("action_override")
    if override_env is not None:
        return str(override_env.payload)

    return actions[0]


def apply_discrete_action(ctx: PipelineContext, action: Any, *, actions: tuple[str, ...]) -> None:
    from quant_platform.core.context import DataEnvelope

    normalized = str(action)
    if normalized not in actions:
        raise ValueError(f"Invalid discrete action: {action!r}")
    ctx.emit(
        DataEnvelope(
            type_key="action",
            payload={"space": "discrete", "value": normalized, "actions": list(actions)},
        )
    )
