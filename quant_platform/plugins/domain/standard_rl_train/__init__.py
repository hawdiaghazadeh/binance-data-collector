"""Standard RL training pipeline plugin (Phase 15)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.manager import PluginManager
from quant_platform.core.plugin import PluginMetadata
from quant_platform.rl_core.pipeline import RLCorePipelineBuilder, register_rl_core_plugins

PLUGIN_METADATA = PluginMetadata(
    name="standard_rl_train",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Standard RL training loop over replay buffer and algorithm plugins",
    input_types=["transitions", "training_config"],
    output_types=["training_result"],
    registry_group="platform.training_pipelines",
)


class StandardRlTraining:
    def run(self, config: dict[str, Any]) -> dict[str, Any]:
        manager = PluginManager()
        register_rl_core_plugins(manager)
        builder = RLCorePipelineBuilder(manager)
        buffer_name = str(config.get("buffer", "uniform_buffer"))
        algorithm_name = str(config.get("algorithm", "ppo"))
        return builder.run(
            config,
            buffer_name=buffer_name,
            algorithm_name=algorithm_name,
        )


def factory(**kwargs) -> StandardRlTraining:
    return StandardRlTraining()


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
