"""Profit-based reward computation (Phase 9)."""

from __future__ import annotations

from quant_platform.core.context import PipelineContext


def calculate_profit_reward(ctx: PipelineContext) -> float:
    """Return step PnL from pnl, step_pnl, or portfolio_state envelopes."""
    for key in ("step_pnl", "pnl"):
        envelope = ctx.optional(key)
        if envelope is not None:
            return float(envelope.payload)

    portfolio_env = ctx.optional("portfolio_state")
    if portfolio_env is not None and isinstance(portfolio_env.payload, dict):
        state = portfolio_env.payload
        if "step_pnl" in state:
            return float(state["step_pnl"])
        if "unrealized_pnl" in state:
            return float(state["unrealized_pnl"])

    return 0.0
