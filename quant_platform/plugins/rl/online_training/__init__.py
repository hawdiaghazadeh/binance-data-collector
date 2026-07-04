"""Online training plugin (G35)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.plugin import PluginMetadata
from quant_platform.rl_product.registry import RL_GROUP
from quant_platform.rl_product.training.loop import OnlineTrainingLoop


PLUGIN_METADATA = PluginMetadata(
    name="online_training",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Online PPO training loop with rollout collection and reward normalization",
    input_types=["training_config", "episodes"],
    output_types=["training_metrics"],
    registry_group=RL_GROUP,
)


class OnlineTrainingPlugin:
    def run(
        self,
        config: dict[str, Any],
        episodes: list,
        *,
        total_timesteps: int | None = None,
    ) -> dict[str, Any]:
        loop = OnlineTrainingLoop.compile(config, episodes)
        metrics = loop.run(total_timesteps=total_timesteps)
        return {
            "timesteps": metrics.timesteps,
            "updates": metrics.updates,
            "episodes": metrics.episodes,
            "last_loss": metrics.last_loss,
            "graph_schema_hash": loop.graph_schema_hash,
        }


def factory(**kwargs) -> OnlineTrainingPlugin:
    return OnlineTrainingPlugin()


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
