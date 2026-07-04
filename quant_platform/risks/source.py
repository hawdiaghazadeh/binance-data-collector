"""Risk context helpers (Phase 13)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import PipelineContext


def resolve_equity(ctx: PipelineContext, *, default: float = 10_000.0) -> float:
    portfolio_env = ctx.optional("portfolio_state")
    if portfolio_env is not None and isinstance(portfolio_env.payload, dict):
        state = portfolio_env.payload
        if "equity" in state:
            return float(state["equity"])
        cash = float(state.get("cash", 0.0))
        unrealized = float(state.get("unrealized_pnl", 0.0))
        return cash + unrealized

    equity_env = ctx.optional("equity")
    if equity_env is not None:
        return float(equity_env.payload)
    return default


def resolve_exposure(ctx: PipelineContext) -> float:
    portfolio_env = ctx.optional("portfolio_state")
    if portfolio_env is not None and isinstance(portfolio_env.payload, dict):
        return float(portfolio_env.payload.get("exposure", 0.0))
    return 0.0


def resolve_trade_stats(ctx: PipelineContext) -> dict[str, float]:
    stats_env = ctx.optional("trade_stats")
    if stats_env is not None and isinstance(stats_env.payload, dict):
        payload = stats_env.payload
        return {
            "win_rate": float(payload.get("win_rate", 0.5)),
            "win_loss_ratio": float(payload.get("win_loss_ratio", 1.0)),
        }
    return {"win_rate": 0.5, "win_loss_ratio": 1.0}
