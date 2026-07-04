"""Dynamic strategy pipeline builder — Phase 12."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.execution_graph import CompiledExecutionGraph, ExecutionStep
from quant_platform.core.manager import PluginManager
from quant_platform.registries.domain import STRATEGY_GROUP


class StrategyPipelineBuilder:
    def __init__(self, manager: PluginManager) -> None:
        self._manager = manager

    def run(self, ctx: PipelineContext, strategy_names: list[str]) -> list[dict[str, Any]]:
        merged: list[dict[str, Any]] = []
        for name in strategy_names:
            strategy = self._manager.get(STRATEGY_GROUP, name)
            strategy.on_bar(ctx)
            merged.extend(strategy.signals(ctx))
        ctx.emit(DataEnvelope(type_key="strategy_signals", payload=merged))
        return merged

    def build_graph(self, strategy_names: list[str]) -> CompiledExecutionGraph:
        names = list(strategy_names)

        def handler(ctx: PipelineContext) -> None:
            self.run(ctx, names)

        return CompiledExecutionGraph(
            (
                ExecutionStep(
                    plugin_name="strategy_pipeline",
                    handler=handler,
                    registry_group=STRATEGY_GROUP,
                ),
            )
        )


def register_strategy_plugins(manager: PluginManager) -> None:
    from quant_platform.plugins.domain.rule_based import PLUGIN_METADATA as RULE_META
    from quant_platform.plugins.domain.rule_based import factory as rule_factory
    from quant_platform.plugins.domain.smc_ict import PLUGIN_METADATA as SMC_META
    from quant_platform.plugins.domain.smc_ict import factory as smc_factory

    reg = manager.registry(STRATEGY_GROUP)
    for meta, factory in [
        (RULE_META, rule_factory),
        (SMC_META, smc_factory),
    ]:
        if meta.name not in {m.name for m in reg.list_plugins()}:
            reg.register(meta, factory)
