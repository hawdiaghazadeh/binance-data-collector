"""Dynamic action pipeline builder — Phase 10."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import PipelineContext
from quant_platform.core.execution_graph import CompiledExecutionGraph, ExecutionStep
from quant_platform.core.manager import PluginManager
from quant_platform.registries.domain import ACTION_GROUP


class ActionPipelineBuilder:
    def __init__(self, manager: PluginManager) -> None:
        self._manager = manager

    def sample_and_apply(self, ctx: PipelineContext, action_name: str) -> Any:
        plugin = self._manager.get(ACTION_GROUP, action_name)
        action = plugin.sample(ctx)
        plugin.apply(ctx, action)
        return action

    def build_graph(self, action_name: str) -> CompiledExecutionGraph:
        def handler(ctx: PipelineContext) -> None:
            self.sample_and_apply(ctx, action_name)

        return CompiledExecutionGraph(
            (
                ExecutionStep(
                    plugin_name=action_name,
                    handler=handler,
                    registry_group=ACTION_GROUP,
                ),
            )
        )

    def run(self, ctx: PipelineContext, action_name: str) -> Any:
        return self.sample_and_apply(ctx, action_name)


def register_action_plugins(manager: PluginManager) -> None:
    from quant_platform.plugins.domain.continuous_action import PLUGIN_METADATA as CONTINUOUS_META
    from quant_platform.plugins.domain.continuous_action import factory as continuous_factory
    from quant_platform.plugins.domain.discrete_action import PLUGIN_METADATA as DISCRETE_META
    from quant_platform.plugins.domain.discrete_action import factory as discrete_factory
    from quant_platform.plugins.domain.hybrid_action import PLUGIN_METADATA as HYBRID_META
    from quant_platform.plugins.domain.hybrid_action import factory as hybrid_factory

    reg = manager.registry(ACTION_GROUP)
    for meta, factory in [
        (DISCRETE_META, discrete_factory),
        (CONTINUOUS_META, continuous_factory),
        (HYBRID_META, hybrid_factory),
    ]:
        if meta.name not in {m.name for m in reg.list_plugins()}:
            reg.register(meta, factory)
