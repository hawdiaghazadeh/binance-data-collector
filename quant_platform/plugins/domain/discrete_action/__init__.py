"""Discrete action plugin (Phase 10)."""

from __future__ import annotations

import random
from typing import Any

from quant_platform.core.context import PipelineContext
from quant_platform.core.plugin import PluginMetadata
from quant_platform.actions.discrete import (
    DEFAULT_DISCRETE_ACTIONS,
    apply_discrete_action,
    sample_discrete_action,
)

PLUGIN_METADATA = PluginMetadata(
    name="discrete_action",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Discrete hold/buy/sell action space for RL agents",
    input_types=["policy_probs", "strategy_signals", "action_override"],
    output_types=["action"],
    registry_group="platform.actions",
)


class DiscreteAction:
    def __init__(
        self,
        actions: tuple[str, ...] = DEFAULT_DISCRETE_ACTIONS,
        exploration: float = 0.0,
        seed: int | None = None,
    ) -> None:
        self._actions = actions
        self._exploration = exploration
        self._rng = random.Random(seed)

    def sample(self, ctx: PipelineContext) -> str:
        return sample_discrete_action(
            ctx,
            actions=self._actions,
            exploration=self._exploration,
            rng=self._rng,
        )

    def apply(self, ctx: PipelineContext, action: Any) -> None:
        apply_discrete_action(ctx, action, actions=self._actions)


def factory(
    *,
    actions: tuple[str, ...] | list[str] | None = None,
    exploration: float = 0.0,
    seed: int | None = None,
    config: dict | None = None,
    **kwargs,
) -> DiscreteAction:
    if config:
        if "actions" in config:
            actions = tuple(str(item) for item in config["actions"])
        exploration = float(config.get("exploration", exploration))
        if "seed" in config:
            seed = int(config["seed"])
    resolved_actions = tuple(actions) if actions is not None else DEFAULT_DISCRETE_ACTIONS
    return DiscreteAction(actions=resolved_actions, exploration=exploration, seed=seed)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
