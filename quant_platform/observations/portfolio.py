"""Portfolio state observation builder (Phase 8)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import PipelineContext


def build_portfolio_observation(ctx: PipelineContext) -> dict[str, Any]:
    """Build portfolio observation from optional portfolio_state envelope."""
    portfolio_env = ctx.optional("portfolio_state")
    if portfolio_env is not None and isinstance(portfolio_env.payload, dict):
        state = portfolio_env.payload
        positions = state.get("positions", {})
        return {
            "cash": float(state.get("cash", 0.0)),
            "equity": float(state.get("equity", 0.0)),
            "positions": dict(positions) if isinstance(positions, dict) else {},
            "exposure": float(state.get("exposure", 0.0)),
            "unrealized_pnl": float(state.get("unrealized_pnl", 0.0)),
        }

    return {
        "cash": 0.0,
        "equity": 0.0,
        "positions": {},
        "exposure": 0.0,
        "unrealized_pnl": 0.0,
    }
