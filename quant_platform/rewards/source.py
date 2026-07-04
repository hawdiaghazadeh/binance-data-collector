"""Resolve return and equity series for reward plugins (Phase 9)."""

from __future__ import annotations

from quant_platform.core.context import PipelineContext
from quant_platform.indicators.compute import extract_closes
from quant_platform.indicators.source import resolve_klines


def resolve_returns(ctx: PipelineContext) -> list[float]:
    returns_env = ctx.optional("returns")
    if returns_env is not None:
        return [float(value) for value in returns_env.payload]

    equity_env = ctx.optional("equity_curve")
    if equity_env is not None:
        equity = [float(value) for value in equity_env.payload]
        returns: list[float] = []
        for index in range(1, len(equity)):
            previous = equity[index - 1]
            if previous == 0:
                continue
            returns.append((equity[index] - previous) / previous)
        return returns

    closes = extract_closes(resolve_klines(ctx))
    returns = []
    for index in range(1, len(closes)):
        previous = closes[index - 1]
        if previous == 0:
            continue
        returns.append((closes[index] - previous) / previous)
    return returns


def resolve_equity_curve(ctx: PipelineContext) -> list[float]:
    equity_env = ctx.optional("equity_curve")
    if equity_env is not None:
        return [float(value) for value in equity_env.payload]

    portfolio_env = ctx.optional("portfolio_state")
    if portfolio_env is not None and isinstance(portfolio_env.payload, dict):
        equity = portfolio_env.payload.get("equity")
        if equity is not None:
            return [float(equity)]

    return []
