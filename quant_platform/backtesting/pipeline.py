"""Backtesting pipeline builder — Phase 17."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.execution_graph import CompiledExecutionGraph, ExecutionStep
from quant_platform.core.manager import PluginManager
from quant_platform.registries.domain import BACKTESTING_GROUP


class BacktestPipelineBuilder:
    def __init__(self, manager: PluginManager) -> None:
        self._manager = manager

    def run(
        self,
        ctx: PipelineContext,
        strategy: Any,
        data: Any,
        *,
        engine_name: str = "event_driven",
    ) -> dict[str, Any]:
        engine = self._manager.get(BACKTESTING_GROUP, engine_name)
        result = engine.run(strategy, data)
        ctx.emit(DataEnvelope(type_key="backtest_result", payload=result))
        if "equity_curve" in result:
            ctx.emit(DataEnvelope(type_key="equity_curve", payload=result["equity_curve"]))
        return result

    def build_graph(self, *, engine_name: str = "event_driven") -> CompiledExecutionGraph:
        def handler(ctx: PipelineContext) -> None:
            request = ctx.require("backtest_request").payload
            self.run(
                ctx,
                request.get("strategy"),
                request.get("data"),
                engine_name=engine_name,
            )

        return CompiledExecutionGraph(
            (
                ExecutionStep(
                    plugin_name="backtest_pipeline",
                    handler=handler,
                    registry_group=BACKTESTING_GROUP,
                ),
            )
        )


def register_backtesting_plugins(manager: PluginManager) -> None:
    from quant_platform.plugins.domain.event_driven import PLUGIN_METADATA as EVENT_META
    from quant_platform.plugins.domain.event_driven import factory as event_factory
    from quant_platform.plugins.domain.vectorized import PLUGIN_METADATA as VECTOR_META
    from quant_platform.plugins.domain.vectorized import factory as vector_factory

    reg = manager.registry(BACKTESTING_GROUP)
    for meta, factory in [(EVENT_META, event_factory), (VECTOR_META, vector_factory)]:
        if meta.name not in {m.name for m in reg.list_plugins()}:
            reg.register(meta, factory)
