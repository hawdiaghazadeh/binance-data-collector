"""Portfolio context helpers (Phase 13)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import PipelineContext


def resolve_portfolio_state(ctx: PipelineContext) -> dict[str, Any] | None:
    portfolio_env = ctx.optional("portfolio_state")
    if portfolio_env is not None and isinstance(portfolio_env.payload, dict):
        return dict(portfolio_env.payload)
    return None


def resolve_execution_result(ctx: PipelineContext) -> dict[str, Any] | None:
    result_env = ctx.optional("execution_result")
    if result_env is not None and isinstance(result_env.payload, dict):
        return dict(result_env.payload)
    return None
