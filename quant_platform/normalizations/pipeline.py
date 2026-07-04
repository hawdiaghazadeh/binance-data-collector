"""Dynamic normalization pipeline builder — Phase 4."""

from __future__ import annotations

from quant_platform.core.context import PipelineContext
from quant_platform.core.execution_graph import CompiledExecutionGraph, ExecutionStep
from quant_platform.core.manager import PluginManager
from quant_platform.registries.domain import NORMALIZATION_GROUP


class NormalizationPipelineBuilder:
    def __init__(self, manager: PluginManager) -> None:
        self._manager = manager

    def build_graph(self, normalizer_names: list[str]) -> CompiledExecutionGraph:
        steps: list[ExecutionStep] = []
        for name in normalizer_names:
            normalizer = self._manager.get(NORMALIZATION_GROUP, name)

            def make_handler(n=normalizer):
                def handler(ctx: PipelineContext) -> None:
                    n.normalize(ctx)

                return handler

            steps.append(
                ExecutionStep(plugin_name=name, handler=make_handler(), registry_group=NORMALIZATION_GROUP)
            )
        return CompiledExecutionGraph(tuple(steps))

    def run(self, ctx: PipelineContext, normalizer_names: list[str]) -> None:
        graph = self.build_graph(normalizer_names)
        graph.execute(ctx)


def register_normalization_plugins(manager: PluginManager) -> None:
    from quant_platform.plugins.domain.symbol_normalizer import PLUGIN_METADATA as SYMBOL_META
    from quant_platform.plugins.domain.symbol_normalizer import factory as symbol_factory
    from quant_platform.plugins.domain.z_score import PLUGIN_METADATA as ZSCORE_META
    from quant_platform.plugins.domain.z_score import factory as zscore_factory

    reg = manager.registry(NORMALIZATION_GROUP)
    for meta, factory in [
        (SYMBOL_META, symbol_factory),
        (ZSCORE_META, zscore_factory),
    ]:
        if meta.name not in {m.name for m in reg.list_plugins()}:
            reg.register(meta, factory)
