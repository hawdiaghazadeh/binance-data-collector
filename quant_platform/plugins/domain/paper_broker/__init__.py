"""Paper broker plugin (Phase 14)."""

from __future__ import annotations

from typing import Any

from quant_platform.brokers.paper import PaperBrokerEngine
from quant_platform.brokers.source import normalize_broker_order
from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.plugin import PluginMetadata
from quant_platform.executions.source import resolve_price
from quant_platform.risks.source import resolve_equity

PLUGIN_METADATA = PluginMetadata(
    name="paper_broker",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Simulated broker routing orders to paper fills",
    input_types=["order", "price", "portfolio_state", "equity"],
    output_types=["broker_result", "execution_result"],
    registry_group="platform.brokers",
)


class PaperBroker:
    def __init__(self, engine: PaperBrokerEngine, ctx: PipelineContext | None = None) -> None:
        self._engine = engine
        self._ctx = ctx

    def submit_order(self, order: Any) -> dict[str, Any]:
        normalized = normalize_broker_order(order)
        price = float(normalized.get("price", resolve_price(self._ctx) if self._ctx else 0.0))
        equity = float(normalized.get("equity", resolve_equity(self._ctx) if self._ctx else 10_000.0))
        result = self._engine.submit_order(normalized, price=price, equity=equity)
        if self._ctx is not None:
            self._ctx.emit(DataEnvelope(type_key="broker_result", payload=result))
            fill = result.get("fill")
            if isinstance(fill, dict):
                self._ctx.emit(DataEnvelope(type_key="execution_result", payload=fill))
        return result

    def cancel_order(self, order_id: str) -> bool:
        return self._engine.cancel_order(order_id)


def factory(
    *,
    fee_rate: float = 0.001,
    slippage_bps: float = 5.0,
    config: dict | None = None,
    **kwargs,
) -> PaperBroker:
    cfg = dict(config or {})
    if cfg:
        fee_rate = float(cfg.get("fee_rate", fee_rate))
        slippage_bps = float(cfg.get("slippage_bps", slippage_bps))
    ctx = cfg.get("context")
    engine = PaperBrokerEngine(fee_rate=fee_rate, slippage_bps=slippage_bps)
    return PaperBroker(engine, ctx=ctx if isinstance(ctx, PipelineContext) else None)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
