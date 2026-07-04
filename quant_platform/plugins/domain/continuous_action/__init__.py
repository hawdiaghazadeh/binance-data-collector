"""Continuous action plugin (Phase 10)."""

from __future__ import annotations

import random
from typing import Any

from quant_platform.core.context import PipelineContext
from quant_platform.core.plugin import PluginMetadata
from quant_platform.actions.continuous import apply_continuous_action, sample_continuous_action

PLUGIN_METADATA = PluginMetadata(
    name="continuous_action",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Continuous position target action space in [low, high]",
    input_types=["policy_mean", "action_override"],
    output_types=["action"],
    registry_group="platform.actions",
)


class ContinuousAction:
    def __init__(
        self,
        low: float = -1.0,
        high: float = 1.0,
        exploration_std: float = 0.0,
        seed: int | None = None,
    ) -> None:
        self._low = low
        self._high = high
        self._exploration_std = exploration_std
        self._rng = random.Random(seed)

    def sample(self, ctx: PipelineContext) -> float:
        return sample_continuous_action(
            ctx,
            low=self._low,
            high=self._high,
            exploration_std=self._exploration_std,
            rng=self._rng,
        )

    def apply(self, ctx: PipelineContext, action: Any) -> None:
        apply_continuous_action(ctx, action, low=self._low, high=self._high)


def factory(
    *,
    low: float = -1.0,
    high: float = 1.0,
    exploration_std: float = 0.0,
    seed: int | None = None,
    config: dict | None = None,
    **kwargs,
) -> ContinuousAction:
    if config:
        low = float(config.get("low", low))
        high = float(config.get("high", high))
        exploration_std = float(config.get("exploration_std", exploration_std))
        if "seed" in config:
            seed = int(config["seed"])
    return ContinuousAction(low=low, high=high, exploration_std=exploration_std, seed=seed)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
