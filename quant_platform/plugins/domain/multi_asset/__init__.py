"""Multi-asset portfolio plugin (Phase 13)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.plugin import PluginMetadata
from quant_platform.executions.source import resolve_price
from quant_platform.portfolios.multi import MultiAssetPortfolioEngine
from quant_platform.portfolios.source import resolve_execution_result, resolve_portfolio_state

PLUGIN_METADATA = PluginMetadata(
    name="multi_asset",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Multi-symbol portfolio state from simulated fills",
    input_types=["execution_result", "portfolio_state", "klines", "price", "prices"],
    output_types=["portfolio_state", "step_pnl"],
    registry_group="platform.portfolios",
)


class MultiAssetPortfolio:
    def __init__(self, engine: MultiAssetPortfolioEngine) -> None:
        self._engine = engine

    def update(self, ctx: PipelineContext) -> None:
        fill = resolve_execution_result(ctx)
        if fill is None:
            return
        prices = self._resolve_prices(ctx, fill)
        state = self._engine.apply_fill(fill, prices=prices)
        ctx.emit(DataEnvelope(type_key="portfolio_state", payload=state))
        if "step_pnl" in state:
            ctx.emit(DataEnvelope(type_key="step_pnl", payload=state["step_pnl"]))

    def positions(self) -> dict[str, Any]:
        return {}

    def _resolve_prices(self, ctx: PipelineContext, fill: dict[str, Any]) -> dict[str, float]:
        prices_env = ctx.optional("prices")
        if prices_env is not None and isinstance(prices_env.payload, dict):
            return {str(k): float(v) for k, v in prices_env.payload.items()}
        symbol = str(fill.get("symbol", "BTCUSDT"))
        return {symbol: resolve_price(ctx)}


def factory(
    *,
    initial_cash: float = 10_000.0,
    config: dict | None = None,
    **kwargs,
) -> MultiAssetPortfolio:
    if config:
        initial_cash = float(config.get("initial_cash", initial_cash))
    engine = MultiAssetPortfolioEngine(initial_cash=initial_cash)
    ctx = kwargs.get("context")
    if ctx is not None:
        existing = resolve_portfolio_state(ctx)
        if existing:
            engine._cash = float(existing.get("cash", initial_cash))
            positions = existing.get("positions", {})
            if isinstance(positions, dict):
                for symbol, pos in positions.items():
                    if isinstance(pos, dict):
                        engine._positions[str(symbol)] = {
                            "quantity": float(pos.get("quantity", 0.0)),
                            "entry_price": float(pos.get("entry_price", 0.0)),
                        }
    return MultiAssetPortfolio(engine)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
