"""Grouped order-flow pipeline — Phase 13."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.execution_graph import CompiledExecutionGraph, ExecutionStep
from quant_platform.core.manager import PluginManager
from quant_platform.executions.source import normalize_order
from quant_platform.registries.domain import EXECUTION_GROUP, PORTFOLIO_GROUP, RISK_GROUP


class OrderFlowPipelineBuilder:
    """Wire execution, risk, and portfolio plugins for a single order."""

    def __init__(self, manager: PluginManager) -> None:
        self._manager = manager

    def process_order(
        self,
        ctx: PipelineContext,
        order: Any,
        *,
        execution_name: str = "simulation_execution",
        risk_name: str = "fixed_risk",
        portfolio_name: str = "single_asset",
    ) -> dict[str, Any]:
        normalized = normalize_order(order)
        risk = self._manager.get(RISK_GROUP, risk_name)

        sized = dict(normalized)
        sized["size"] = risk.position_size(ctx)

        if not risk.check(ctx, sized):
            result = {"status": "rejected", "order": sized, "reason": "risk_check_failed"}
            ctx.emit(DataEnvelope(type_key="execution_result", payload=result))
            return result

        ctx.emit(DataEnvelope(type_key="order", payload=sized))

        execution = self._manager.get(EXECUTION_GROUP, execution_name)
        fill = execution.execute_order(ctx, sized)
        ctx.emit(DataEnvelope(type_key="execution_result", payload=fill))

        portfolio = self._manager.get(PORTFOLIO_GROUP, portfolio_name)
        portfolio.update(ctx)

        return fill if isinstance(fill, dict) else {"status": "filled", "order": sized}

    def build_graph(
        self,
        *,
        execution_name: str = "simulation_execution",
        risk_name: str = "fixed_risk",
        portfolio_name: str = "single_asset",
    ) -> CompiledExecutionGraph:
        def handler(ctx: PipelineContext) -> None:
            order_env = ctx.require("order")
            self.process_order(
                ctx,
                order_env.payload,
                execution_name=execution_name,
                risk_name=risk_name,
                portfolio_name=portfolio_name,
            )

        return CompiledExecutionGraph(
            (
                ExecutionStep(
                    plugin_name="order_flow",
                    handler=handler,
                    registry_group=EXECUTION_GROUP,
                ),
            )
        )


def register_execution_plugins(manager: PluginManager) -> None:
    from quant_platform.plugins.domain.simulation_execution import PLUGIN_METADATA as EXEC_META
    from quant_platform.plugins.domain.simulation_execution import factory as exec_factory

    reg = manager.registry(EXECUTION_GROUP)
    if EXEC_META.name not in {m.name for m in reg.list_plugins()}:
        reg.register(EXEC_META, exec_factory)


def register_risk_plugins(manager: PluginManager) -> None:
    from quant_platform.plugins.domain.fixed_risk import PLUGIN_METADATA as FIXED_META
    from quant_platform.plugins.domain.fixed_risk import factory as fixed_factory
    from quant_platform.plugins.domain.kelly_risk import PLUGIN_METADATA as KELLY_META
    from quant_platform.plugins.domain.kelly_risk import factory as kelly_factory

    reg = manager.registry(RISK_GROUP)
    for meta, factory in [(FIXED_META, fixed_factory), (KELLY_META, kelly_factory)]:
        if meta.name not in {m.name for m in reg.list_plugins()}:
            reg.register(meta, factory)


def register_portfolio_plugins(manager: PluginManager) -> None:
    from quant_platform.plugins.domain.multi_asset import PLUGIN_METADATA as MULTI_META
    from quant_platform.plugins.domain.multi_asset import factory as multi_factory
    from quant_platform.plugins.domain.single_asset import PLUGIN_METADATA as SINGLE_META
    from quant_platform.plugins.domain.single_asset import factory as single_factory

    reg = manager.registry(PORTFOLIO_GROUP)
    for meta, factory in [(SINGLE_META, single_factory), (MULTI_META, multi_factory)]:
        if meta.name not in {m.name for m in reg.list_plugins()}:
            reg.register(meta, factory)


def register_order_flow_plugins(manager: PluginManager) -> None:
    register_execution_plugins(manager)
    register_risk_plugins(manager)
    register_portfolio_plugins(manager)
