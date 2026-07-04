"""Dynamic indicator pipeline builder — Phase 5."""

from __future__ import annotations

from quant_platform.core.context import PipelineContext
from quant_platform.core.execution_graph import CompiledExecutionGraph, ExecutionStep
from quant_platform.core.manager import PluginManager
from quant_platform.registries.domain import INDICATOR_GROUP


class IndicatorPipelineBuilder:
    def __init__(self, manager: PluginManager) -> None:
        self._manager = manager

    def build_graph(self, indicator_names: list[str]) -> CompiledExecutionGraph:
        steps: list[ExecutionStep] = []
        for name in indicator_names:
            indicator = self._manager.get(INDICATOR_GROUP, name)

            def make_handler(item=indicator):
                def handler(ctx: PipelineContext) -> None:
                    item.compute(ctx)

                return handler

            steps.append(
                ExecutionStep(plugin_name=name, handler=make_handler(), registry_group=INDICATOR_GROUP)
            )
        return CompiledExecutionGraph(tuple(steps))

    def run(self, ctx: PipelineContext, indicator_names: list[str]) -> None:
        graph = self.build_graph(indicator_names)
        graph.execute(ctx)


def register_indicator_plugins(manager: PluginManager) -> None:
    from quant_platform.plugins.domain.ema_indicator import PLUGIN_METADATA as EMA_META
    from quant_platform.plugins.domain.ema_indicator import factory as ema_factory
    from quant_platform.plugins.domain.macd_indicator import PLUGIN_METADATA as MACD_META
    from quant_platform.plugins.domain.macd_indicator import factory as macd_factory
    from quant_platform.plugins.domain.rsi_indicator import PLUGIN_METADATA as RSI_META
    from quant_platform.plugins.domain.rsi_indicator import factory as rsi_factory

    reg = manager.registry(INDICATOR_GROUP)
    for meta, factory in [
        (EMA_META, ema_factory),
        (RSI_META, rsi_factory),
        (MACD_META, macd_factory),
    ]:
        if meta.name not in {m.name for m in reg.list_plugins()}:
            reg.register(meta, factory)
