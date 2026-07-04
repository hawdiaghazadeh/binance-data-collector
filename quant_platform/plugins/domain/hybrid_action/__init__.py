"""Hybrid action plugin (Phase 10)."""

from __future__ import annotations

import random
from typing import Any

from quant_platform.core.context import PipelineContext
from quant_platform.core.plugin import PluginMetadata
from quant_platform.actions.hybrid import apply_hybrid_action, sample_hybrid_action

PLUGIN_METADATA = PluginMetadata(
    name="hybrid_action",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Hybrid side + size action space for RL agents",
    input_types=["policy_probs", "policy_mean", "strategy_signals", "action_override"],
    output_types=["action"],
    registry_group="platform.actions",
)


class HybridAction:
    def __init__(
        self,
        exploration: float = 0.0,
        exploration_std: float = 0.0,
        size_low: float = 0.0,
        size_high: float = 1.0,
        seed: int | None = None,
    ) -> None:
        self._exploration = exploration
        self._exploration_std = exploration_std
        self._size_low = size_low
        self._size_high = size_high
        self._rng = random.Random(seed)

    def sample(self, ctx: PipelineContext) -> dict[str, Any]:
        return sample_hybrid_action(
            ctx,
            size_low=self._size_low,
            size_high=self._size_high,
            exploration=self._exploration,
            exploration_std=self._exploration_std,
            rng=self._rng,
        )

    def apply(self, ctx: PipelineContext, action: Any) -> None:
        apply_hybrid_action(ctx, action)


def factory(
    *,
    exploration: float = 0.0,
    exploration_std: float = 0.0,
    size_low: float = 0.0,
    size_high: float = 1.0,
    seed: int | None = None,
    config: dict | None = None,
    **kwargs,
) -> HybridAction:
    if config:
        exploration = float(config.get("exploration", exploration))
        exploration_std = float(config.get("exploration_std", exploration_std))
        size_low = float(config.get("size_low", size_low))
        size_high = float(config.get("size_high", size_high))
        if "seed" in config:
            seed = int(config["seed"])
    return HybridAction(
        exploration=exploration,
        exploration_std=exploration_std,
        size_low=size_low,
        size_high=size_high,
        seed=seed,
    )


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
