"""Live trading pipeline builder — Phase 19."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.execution_graph import CompiledExecutionGraph, ExecutionStep
from quant_platform.core.manager import PluginManager
from quant_platform.live_trading.source import live_session_config
from quant_platform.registries.domain import LIVE_TRADING_GROUP


class LiveTradingPipelineBuilder:
    def __init__(self, manager: PluginManager) -> None:
        self._manager = manager

    def run(
        self,
        ctx: PipelineContext,
        *,
        strategy: Any,
        exchange: Any,
        bars: list[Any] | None = None,
        symbol: str = "BTCUSDT",
        engine_name: str = "live_engine",
        **config: Any,
    ) -> dict[str, Any]:
        engine = self._manager.get(
            LIVE_TRADING_GROUP,
            engine_name,
            config=live_session_config(
                strategy=strategy,
                exchange=exchange,
                bars=bars or [],
                symbol=symbol,
                **config,
            ),
        )
        engine.start()
        engine.stop()
        result = engine.summary
        ctx.emit(DataEnvelope(type_key="live_trading_result", payload=result))
        if "equity_curve" in result:
            ctx.emit(DataEnvelope(type_key="equity_curve", payload=result["equity_curve"]))
        if "portfolio_state" in result:
            ctx.emit(DataEnvelope(type_key="portfolio_state", payload=result["portfolio_state"]))
        if "tickers" in result:
            ctx.emit(DataEnvelope(type_key="ticker", payload=result["tickers"][-1]))
        return result

    def build_graph(self, *, engine_name: str = "live_engine") -> CompiledExecutionGraph:
        def handler(ctx: PipelineContext) -> None:
            request = ctx.require("live_trading_request").payload
            self.run(
                ctx,
                strategy=request.get("strategy"),
                exchange=request.get("exchange"),
                bars=request.get("bars"),
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
                    plugin_name="live_trading",
                    handler=handler,
                    registry_group=LIVE_TRADING_GROUP,
                ),
            )
        )


def register_live_trading_plugins(manager: PluginManager) -> None:
    from quant_platform.plugins.domain.live_engine import PLUGIN_METADATA as LIVE_META
    from quant_platform.plugins.domain.live_engine import factory as live_factory

    reg = manager.registry(LIVE_TRADING_GROUP)
    if LIVE_META.name not in {m.name for m in reg.list_plugins()}:
        reg.register(LIVE_META, live_factory)
