"""Single-asset portfolio plugin (Phase 13)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.plugin import PluginMetadata
from quant_platform.executions.source import resolve_price
from quant_platform.portfolios.single import SingleAssetPortfolioEngine
from quant_platform.portfolios.source import resolve_execution_result, resolve_portfolio_state

PLUGIN_METADATA = PluginMetadata(
    name="single_asset",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Single-symbol portfolio state from simulated fills",
    input_types=["execution_result", "portfolio_state", "klines", "price"],
    output_types=["portfolio_state", "step_pnl"],
    registry_group="platform.portfolios",
)


class SingleAssetPortfolio:
    def __init__(self, engine: SingleAssetPortfolioEngine) -> None:
        self._engine = engine

    def update(self, ctx: PipelineContext) -> None:
        fill = resolve_execution_result(ctx)
        if fill is None:
            return
        price = resolve_price(ctx)
        state = self._engine.apply_fill(fill, price=price)
        ctx.emit(DataEnvelope(type_key="portfolio_state", payload=state))
        if "step_pnl" in state:
            ctx.emit(DataEnvelope(type_key="step_pnl", payload=state["step_pnl"]))

    def positions(self) -> dict[str, Any]:
        return dict(self._engine.state(price=0.0).get("positions", {}))


def factory(
    *,
    symbol: str = "BTCUSDT",
    initial_cash: float = 10_000.0,
    config: dict | None = None,
    **kwargs,
) -> SingleAssetPortfolio:
    if config:
        symbol = str(config.get("symbol", symbol))
        initial_cash = float(config.get("initial_cash", initial_cash))
    existing = resolve_portfolio_state(kwargs.get("context")) if kwargs.get("context") else None
    engine = SingleAssetPortfolioEngine(symbol=symbol, initial_cash=initial_cash)
    if existing:
        engine._cash = float(existing.get("cash", initial_cash))
        positions = existing.get("positions", {})
        if isinstance(positions, dict) and symbol in positions:
            pos = positions[symbol]
            engine._quantity = float(pos.get("quantity", 0.0))
            engine._entry_price = float(pos.get("entry_price", 0.0))
    return SingleAssetPortfolio(engine)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
