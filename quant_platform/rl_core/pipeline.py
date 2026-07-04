"""Grouped RL core pipeline — Phase 15."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.execution_graph import CompiledExecutionGraph, ExecutionStep
from quant_platform.core.manager import PluginManager
from quant_platform.registries.domain import REPLAY_BUFFER_GROUP, RL_ALGORITHM_GROUP, TRAINING_PIPELINE_GROUP
from quant_platform.training_pipelines.loop import run_training_loop


class RLCorePipelineBuilder:
    """Wire replay buffer, RL algorithm, and training loop."""

    def __init__(self, manager: PluginManager) -> None:
        self._manager = manager

    def run(
        self,
        config: dict[str, Any],
        *,
        buffer_name: str = "uniform_buffer",
        algorithm_name: str = "ppo",
    ) -> dict[str, Any]:
        buffer_config = {"capacity": int(config.get("buffer_capacity", 10_000))}
        buffer = self._manager.get(REPLAY_BUFFER_GROUP, buffer_name, config=buffer_config)
        algorithm = self._manager.get(
            RL_ALGORITHM_GROUP,
            algorithm_name,
            config=dict(config.get("algorithm", {})),
        )
        return run_training_loop(config, buffer=buffer, algorithm=algorithm)

    def build_graph(
        self,
        *,
        buffer_name: str = "uniform_buffer",
        algorithm_name: str = "ppo",
    ) -> CompiledExecutionGraph:
        def handler(ctx: PipelineContext) -> None:
            request = ctx.require("training_request").payload
            result = self.run(
                dict(request),
                buffer_name=buffer_name,
                algorithm_name=algorithm_name,
            )
            ctx.emit(DataEnvelope(type_key="training_result", payload=result))

        return CompiledExecutionGraph(
            (
                ExecutionStep(
                    plugin_name="rl_core",
                    handler=handler,
                    registry_group=TRAINING_PIPELINE_GROUP,
                ),
            )
        )


def register_replay_buffer_plugins(manager: PluginManager) -> None:
    from quant_platform.plugins.domain.uniform_buffer import PLUGIN_METADATA as UNIFORM_META
    from quant_platform.plugins.domain.uniform_buffer import factory as uniform_factory

    reg = manager.registry(REPLAY_BUFFER_GROUP)
    if UNIFORM_META.name not in {m.name for m in reg.list_plugins()}:
        reg.register(UNIFORM_META, uniform_factory)


def register_rl_algorithm_plugins(manager: PluginManager) -> None:
    from quant_platform.plugins.domain.ppo import PLUGIN_METADATA as PPO_META
    from quant_platform.plugins.domain.ppo import factory as ppo_factory
    from quant_platform.plugins.domain.sac import PLUGIN_METADATA as SAC_META
    from quant_platform.plugins.domain.sac import factory as sac_factory

    reg = manager.registry(RL_ALGORITHM_GROUP)
    for meta, factory in [(PPO_META, ppo_factory), (SAC_META, sac_factory)]:
        if meta.name not in {m.name for m in reg.list_plugins()}:
            reg.register(meta, factory)


def register_training_pipeline_plugins(manager: PluginManager) -> None:
    from quant_platform.plugins.domain.standard_rl_train import PLUGIN_METADATA as TRAIN_META
    from quant_platform.plugins.domain.standard_rl_train import factory as train_factory

    reg = manager.registry(TRAINING_PIPELINE_GROUP)
    if TRAIN_META.name not in {m.name for m in reg.list_plugins()}:
        reg.register(TRAIN_META, train_factory)


def register_rl_core_plugins(manager: PluginManager) -> None:
    register_replay_buffer_plugins(manager)
    register_rl_algorithm_plugins(manager)
    register_training_pipeline_plugins(manager)
