"""Paper trading pipeline builder — Phase 18."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.execution_graph import CompiledExecutionGraph, ExecutionStep
from quant_platform.core.manager import PluginManager
from quant_platform.paper_trading.source import session_config
from quant_platform.registries.domain import PAPER_TRADING_GROUP


class PaperTradingPipelineBuilder:
    def __init__(self, manager: PluginManager) -> None:
        self._manager = manager

    def run(
        self,
        ctx: PipelineContext,
        *,
        strategy: Any,
        bars: list[Any],
        symbol: str = "BTCUSDT",
        engine_name: str = "paper_engine",
        **config: Any,
    ) -> dict[str, Any]:
        engine = self._manager.get(
            PAPER_TRADING_GROUP,
            engine_name,
            config=session_config(strategy=strategy, bars=bars, symbol=symbol, **config),
        )
        engine.start()
        result = engine.stop()
        ctx.emit(DataEnvelope(type_key="paper_trading_result", payload=result))
        if "equity_curve" in result:
            ctx.emit(DataEnvelope(type_key="equity_curve", payload=result["equity_curve"]))
        if "portfolio_state" in result:
            ctx.emit(DataEnvelope(type_key="portfolio_state", payload=result["portfolio_state"]))
        return result

    def build_graph(self, *, engine_name: str = "paper_engine") -> CompiledExecutionGraph:
        def handler(ctx: PipelineContext) -> None:
            request = ctx.require("paper_trading_request").payload
            self.run(
                ctx,
                strategy=request.get("strategy"),
                bars=request.get("bars", []),
                symbol=str(request.get("symbol", "BTCUSDT")),
                engine_name=engine_name,
                **{
                    key: request[key]
                    for key in ("initial_cash", "fee_rate", "slippage_bps", "risk_fraction")
                    if key in request
                },
            )

        return CompiledExecutionGraph(
            (
                ExecutionStep(
                    plugin_name="paper_trading",
                    handler=handler,
                    registry_group=PAPER_TRADING_GROUP,
                ),
            )
        )


def register_paper_trading_plugins(manager: PluginManager) -> None:
    from quant_platform.plugins.domain.paper_engine import PLUGIN_METADATA as PAPER_META
    from quant_platform.plugins.domain.paper_engine import factory as paper_factory

    reg = manager.registry(PAPER_TRADING_GROUP)
    if PAPER_META.name not in {m.name for m in reg.list_plugins()}:
        reg.register(PAPER_META, paper_factory)
