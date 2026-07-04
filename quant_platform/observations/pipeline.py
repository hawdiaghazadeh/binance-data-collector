"""Dynamic observation pipeline builder — Phase 8."""

from __future__ import annotations

from quant_platform.core.context import PipelineContext
from quant_platform.core.execution_graph import CompiledExecutionGraph, ExecutionStep
from quant_platform.core.manager import PluginManager
from quant_platform.registries.domain import OBSERVATION_GROUP


class ObservationPipelineBuilder:
    def __init__(self, manager: PluginManager) -> None:
        self._manager = manager

    def build_graph(self, observation_names: list[str]) -> CompiledExecutionGraph:
        steps: list[ExecutionStep] = []
        for name in observation_names:
            builder = self._manager.get(OBSERVATION_GROUP, name)

            def make_handler(item=builder):
                def handler(ctx: PipelineContext) -> None:
                    item.build(ctx)

                return handler

            steps.append(
                ExecutionStep(
                    plugin_name=name,
                    handler=make_handler(),
                    registry_group=OBSERVATION_GROUP,
                )
            )
        return CompiledExecutionGraph(tuple(steps))

    def run(self, ctx: PipelineContext, observation_names: list[str]) -> None:
        graph = self.build_graph(observation_names)
        graph.execute(ctx)


def register_observation_plugins(manager: PluginManager) -> None:
    from quant_platform.plugins.domain.candle_observation import PLUGIN_METADATA as CANDLE_META
    from quant_platform.plugins.domain.candle_observation import factory as candle_factory
    from quant_platform.plugins.domain.portfolio_observation import PLUGIN_METADATA as PORTFOLIO_META
    from quant_platform.plugins.domain.portfolio_observation import factory as portfolio_factory
    from quant_platform.plugins.domain.risk_observation import PLUGIN_METADATA as RISK_META
    from quant_platform.plugins.domain.risk_observation import factory as risk_factory

    reg = manager.registry(OBSERVATION_GROUP)
    for meta, factory in [
        (CANDLE_META, candle_factory),
        (PORTFOLIO_META, portfolio_factory),
        (RISK_META, risk_factory),
    ]:
        if meta.name not in {m.name for m in reg.list_plugins()}:
            reg.register(meta, factory)
