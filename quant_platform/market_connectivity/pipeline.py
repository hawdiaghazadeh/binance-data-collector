"""Grouped exchange + broker pipeline — Phase 14."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.execution_graph import CompiledExecutionGraph, ExecutionStep
from quant_platform.core.manager import PluginManager
from quant_platform.executions.source import normalize_order, resolve_price
from quant_platform.risks.source import resolve_equity
from quant_platform.registries.domain import BROKER_GROUP, EXCHANGE_GROUP


class MarketConnectivityPipelineBuilder:
    """Fetch market data from an exchange and route orders through a broker."""

    def __init__(self, manager: PluginManager) -> None:
        self._manager = manager

    def fetch_market_data(
        self,
        ctx: PipelineContext,
        symbol: str,
        timeframe: str,
        *,
        exchange_name: str = "binance_exchange",
        limit: int = 100,
    ) -> dict[str, Any]:
        exchange = self._manager.get(EXCHANGE_GROUP, exchange_name)
        ticker = exchange.fetch_ticker(symbol)
        candles = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        ctx.emit(DataEnvelope(type_key="price", payload=ticker["price"]))
        ctx.emit(DataEnvelope(type_key="ticker", payload=ticker))
        ctx.emit(DataEnvelope(type_key="klines", payload=candles))
        return {"ticker": ticker, "klines": candles}

    def submit_order(
        self,
        ctx: PipelineContext,
        order: Any,
        *,
        broker_name: str = "paper_broker",
    ) -> dict[str, Any]:
        normalized = normalize_order(order)
        if "price" not in normalized:
            normalized["price"] = resolve_price(ctx)
        if "equity" not in normalized:
            normalized["equity"] = resolve_equity(ctx)

        broker = self._manager.get(BROKER_GROUP, broker_name, config={"context": ctx})
        result = broker.submit_order(normalized)
        ctx.emit(DataEnvelope(type_key="broker_result", payload=result))
        fill = result.get("fill")
        if isinstance(fill, dict):
            ctx.emit(DataEnvelope(type_key="execution_result", payload=fill))
        return result

    def fetch_and_submit(
        self,
        ctx: PipelineContext,
        symbol: str,
        timeframe: str,
        order: Any,
        *,
        exchange_name: str = "binance_exchange",
        broker_name: str = "paper_broker",
        limit: int = 100,
    ) -> dict[str, Any]:
        self.fetch_market_data(
            ctx,
            symbol,
            timeframe,
            exchange_name=exchange_name,
            limit=limit,
        )
        return self.submit_order(ctx, order, broker_name=broker_name)

    def build_graph(
        self,
        *,
        exchange_name: str = "binance_exchange",
        broker_name: str = "paper_broker",
    ) -> CompiledExecutionGraph:
        def handler(ctx: PipelineContext) -> None:
            params = ctx.require("market_request").payload
            self.fetch_and_submit(
                ctx,
                str(params["symbol"]),
                str(params["timeframe"]),
                params["order"],
                exchange_name=exchange_name,
                broker_name=broker_name,
                limit=int(params.get("limit", 100)),
            )

        return CompiledExecutionGraph(
            (
                ExecutionStep(
                    plugin_name="market_connectivity",
                    handler=handler,
                    registry_group=EXCHANGE_GROUP,
                ),
            )
        )


def register_exchange_plugins(manager: PluginManager) -> None:
    from quant_platform.plugins.domain.binance_exchange import PLUGIN_METADATA as BINANCE_META
    from quant_platform.plugins.domain.binance_exchange import factory as binance_factory

    reg = manager.registry(EXCHANGE_GROUP)
    if BINANCE_META.name not in {m.name for m in reg.list_plugins()}:
        reg.register(BINANCE_META, binance_factory)


def register_broker_plugins(manager: PluginManager) -> None:
    from quant_platform.plugins.domain.paper_broker import PLUGIN_METADATA as PAPER_META
    from quant_platform.plugins.domain.paper_broker import factory as paper_factory

    reg = manager.registry(BROKER_GROUP)
    if PAPER_META.name not in {m.name for m in reg.list_plugins()}:
        reg.register(PAPER_META, paper_factory)


def register_market_connectivity_plugins(manager: PluginManager) -> None:
    register_exchange_plugins(manager)
    register_broker_plugins(manager)
