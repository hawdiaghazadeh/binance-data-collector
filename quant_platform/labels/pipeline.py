"""Dynamic label pipeline builder — Phase 7."""

from __future__ import annotations

from quant_platform.core.context import PipelineContext
from quant_platform.core.execution_graph import CompiledExecutionGraph, ExecutionStep
from quant_platform.core.manager import PluginManager
from quant_platform.registries.domain import LABEL_GROUP


class LabelPipelineBuilder:
    def __init__(self, manager: PluginManager) -> None:
        self._manager = manager

    def build_graph(self, label_names: list[str]) -> CompiledExecutionGraph:
        steps: list[ExecutionStep] = []
        for name in label_names:
            labeler = self._manager.get(LABEL_GROUP, name)

            def make_handler(item=labeler):
                def handler(ctx: PipelineContext) -> None:
                    item.generate(ctx)

                return handler

            steps.append(
                ExecutionStep(plugin_name=name, handler=make_handler(), registry_group=LABEL_GROUP)
            )
        return CompiledExecutionGraph(tuple(steps))

    def run(self, ctx: PipelineContext, label_names: list[str]) -> None:
        graph = self.build_graph(label_names)
        graph.execute(ctx)


def register_label_plugins(manager: PluginManager) -> None:
    from quant_platform.plugins.domain.direction_label import PLUGIN_METADATA as DIRECTION_META
    from quant_platform.plugins.domain.direction_label import factory as direction_factory
    from quant_platform.plugins.domain.regime_label import PLUGIN_METADATA as REGIME_META
    from quant_platform.plugins.domain.regime_label import factory as regime_factory

    reg = manager.registry(LABEL_GROUP)
    for meta, factory in [
        (DIRECTION_META, direction_factory),
        (REGIME_META, regime_factory),
    ]:
        if meta.name not in {m.name for m in reg.list_plugins()}:
            reg.register(meta, factory)
