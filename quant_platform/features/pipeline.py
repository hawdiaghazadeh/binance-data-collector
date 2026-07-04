"""Dynamic feature pipeline builder."""

from __future__ import annotations

from quant_platform.core.context import PipelineContext
from quant_platform.core.execution_graph import CompiledExecutionGraph, ExecutionStep
from quant_platform.core.manager import PluginManager
from quant_platform.registries.feature import FEATURE_GROUP


class FeaturePipelineBuilder:
    def __init__(self, manager: PluginManager) -> None:
        self._manager = manager

    def build_graph(self, feature_names: list[str]) -> CompiledExecutionGraph:
        steps: list[ExecutionStep] = []
        for name in feature_names:
            feature = self._manager.get(FEATURE_GROUP, name)

            def make_handler(f=feature):
                def handler(ctx: PipelineContext) -> None:
                    f.compute(ctx)

                return handler

            steps.append(ExecutionStep(plugin_name=name, handler=make_handler(), registry_group=FEATURE_GROUP))
        return CompiledExecutionGraph(tuple(steps))

    def run(self, ctx: PipelineContext, feature_names: list[str]) -> None:
        graph = self.build_graph(feature_names)
        graph.execute(ctx)


def register_feature_plugins(manager: PluginManager) -> None:
    from quant_platform.plugins.atr_feature import PLUGIN_METADATA as ATR_META
    from quant_platform.plugins.atr_feature import factory as atr_factory
    from quant_platform.plugins.ohlc_feature import PLUGIN_METADATA as OHLC_META
    from quant_platform.plugins.ohlc_feature import factory as ohlc_factory
    from quant_platform.plugins.volume_feature import PLUGIN_METADATA as VOL_META
    from quant_platform.plugins.volume_feature import factory as vol_factory
    from quant_platform.plugins.vwap_feature import PLUGIN_METADATA as VWAP_META
    from quant_platform.plugins.vwap_feature import factory as vwap_factory

    reg = manager.registry(FEATURE_GROUP)
    for meta, factory in [
        (OHLC_META, ohlc_factory),
        (VOL_META, vol_factory),
        (ATR_META, atr_factory),
        (VWAP_META, vwap_factory),
    ]:
        if meta.name not in {m.name for m in reg.list_plugins()}:
            reg.register(meta, factory)
