"""Dynamic market structure pipeline builder — Phase 6."""

from __future__ import annotations

from quant_platform.core.context import PipelineContext
from quant_platform.core.execution_graph import CompiledExecutionGraph, ExecutionStep
from quant_platform.core.manager import PluginManager
from quant_platform.registries.domain import MARKET_STRUCTURE_GROUP


class MarketStructurePipelineBuilder:
    def __init__(self, manager: PluginManager) -> None:
        self._manager = manager

    def build_graph(self, analyzer_names: list[str]) -> CompiledExecutionGraph:
        steps: list[ExecutionStep] = []
        for name in analyzer_names:
            analyzer = self._manager.get(MARKET_STRUCTURE_GROUP, name)

            def make_handler(item=analyzer):
                def handler(ctx: PipelineContext) -> None:
                    item.analyze(ctx)

                return handler

            steps.append(
                ExecutionStep(
                    plugin_name=name,
                    handler=make_handler(),
                    registry_group=MARKET_STRUCTURE_GROUP,
                )
            )
        return CompiledExecutionGraph(tuple(steps))

    def run(self, ctx: PipelineContext, analyzer_names: list[str]) -> None:
        graph = self.build_graph(analyzer_names)
        graph.execute(ctx)


def register_market_structure_plugins(manager: PluginManager) -> None:
    from quant_platform.plugins.domain.bos_choch import PLUGIN_METADATA as BOS_META
    from quant_platform.plugins.domain.bos_choch import factory as bos_factory
    from quant_platform.plugins.domain.fvg import PLUGIN_METADATA as FVG_META
    from quant_platform.plugins.domain.fvg import factory as fvg_factory
    from quant_platform.plugins.domain.order_blocks import PLUGIN_METADATA as OB_META
    from quant_platform.plugins.domain.order_blocks import factory as ob_factory

    reg = manager.registry(MARKET_STRUCTURE_GROUP)
    for meta, factory in [
        (BOS_META, bos_factory),
        (FVG_META, fvg_factory),
        (OB_META, ob_factory),
    ]:
        if meta.name not in {m.name for m in reg.list_plugins()}:
            reg.register(meta, factory)
