"""Risk metrics observation builder (Phase 8)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import PipelineContext
from quant_platform.observations.portfolio import build_portfolio_observation


def build_risk_observation(ctx: PipelineContext, *, max_exposure: float = 1.0) -> dict[str, Any]:
    """Build risk observation from risk_state, portfolio, and optional ATR envelope."""
    risk_env = ctx.optional("risk_state")
    if risk_env is not None and isinstance(risk_env.payload, dict):
        return dict(risk_env.payload)

    portfolio = build_portfolio_observation(ctx)
    exposure = float(portfolio["exposure"])
    utilization = exposure / max_exposure if max_exposure > 0 else 0.0

    volatility: float | None = None
    atr_env = ctx.optional("atr")
    if atr_env is not None and isinstance(atr_env.payload, list):
        values = [value for value in atr_env.payload if value is not None]
        if values:
            volatility = float(values[-1])

    return {
        "exposure": exposure,
        "max_exposure": max_exposure,
        "risk_utilization": min(utilization, 1.0),
        "within_limits": exposure <= max_exposure,
        "volatility": volatility,
        "drawdown": float(portfolio.get("drawdown", 0.0)),
    }
