"""SAC algorithm plugin (Phase 15)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.plugin import PluginMetadata
from quant_platform.rl_algorithms.sac import sac_train_step

PLUGIN_METADATA = PluginMetadata(
    name="sac",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Soft Actor-Critic skeleton for offline batch updates",
    input_types=["replay_batch"],
    output_types=["training_metrics"],
    registry_group="platform.rl_algorithms",
)


class SacAlgorithm:
    def __init__(
        self,
        *,
        learning_rate: float = 3e-4,
        entropy_coef: float = 0.2,
        critic_coef: float = 0.5,
    ) -> None:
        self._learning_rate = learning_rate
        self._entropy_coef = entropy_coef
        self._critic_coef = critic_coef

    def train_step(self, batch: list[Any]) -> dict[str, Any]:
        return sac_train_step(
            batch,
            learning_rate=self._learning_rate,
            entropy_coef=self._entropy_coef,
            critic_coef=self._critic_coef,
        )


def factory(
    *,
    learning_rate: float = 3e-4,
    entropy_coef: float = 0.2,
    critic_coef: float = 0.5,
    config: dict | None = None,
    **kwargs,
) -> SacAlgorithm:
    if config:
        learning_rate = float(config.get("learning_rate", learning_rate))
        entropy_coef = float(config.get("entropy_coef", entropy_coef))
        critic_coef = float(config.get("critic_coef", critic_coef))
    return SacAlgorithm(
        learning_rate=learning_rate,
        entropy_coef=entropy_coef,
        critic_coef=critic_coef,
    )


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
