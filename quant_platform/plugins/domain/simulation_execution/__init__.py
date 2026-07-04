"""Simulated order execution plugin (Phase 13)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.plugin import PluginMetadata
from quant_platform.executions.simulation import simulate_fill
from quant_platform.executions.source import normalize_order, resolve_price
from quant_platform.risks.source import resolve_equity

PLUGIN_METADATA = PluginMetadata(
    name="simulation_execution",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Simulated market fill with slippage and fees",
    input_types=["order", "klines", "ohlc", "price", "portfolio_state"],
    output_types=["execution_result"],
    registry_group="platform.executions",
)


class SimulationExecution:
    def __init__(
        self,
        *,
        fee_rate: float = 0.001,
        slippage_bps: float = 5.0,
    ) -> None:
        self._fee_rate = fee_rate
        self._slippage_bps = slippage_bps

    def execute_order(self, ctx: PipelineContext, order: Any) -> dict[str, Any]:
        normalized = normalize_order(order)
        price = resolve_price(ctx)
        equity = resolve_equity(ctx)
        fill = simulate_fill(
            normalized,
            price=price,
            equity=equity,
            fee_rate=self._fee_rate,
            slippage_bps=self._slippage_bps,
        )
        ctx.emit(DataEnvelope(type_key="execution_result", payload=fill))
        return fill


def factory(
    *,
    fee_rate: float = 0.001,
    slippage_bps: float = 5.0,
    config: dict | None = None,
    **kwargs,
) -> SimulationExecution:
    if config:
        fee_rate = float(config.get("fee_rate", fee_rate))
        slippage_bps = float(config.get("slippage_bps", slippage_bps))
    return SimulationExecution(fee_rate=fee_rate, slippage_bps=slippage_bps)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
