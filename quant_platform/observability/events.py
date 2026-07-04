"""Shared observability event helpers (Phase 20)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from quant_platform.core.context import PipelineContext


@dataclass
class ObservabilityEvent:
    message: str = ""
    channel: str = "default"
    metrics: list[tuple[str, float, dict[str, str]]] = field(default_factory=list)
    tags: dict[str, str] = field(default_factory=dict)


def extract_metrics_from_context(ctx: PipelineContext) -> list[tuple[str, float, dict[str, str]]]:
    metrics: list[tuple[str, float, dict[str, str]]] = []

    equity_env = ctx.optional("equity_curve")
    if equity_env is not None and isinstance(equity_env.payload, list) and equity_env.payload:
        metrics.append(("equity.latest", float(equity_env.payload[-1]), {}))
        metrics.append(("equity.points", float(len(equity_env.payload)), {}))

    for key in ("paper_trading_result", "live_trading_result", "backtest_result"):
        result_env = ctx.optional(key)
        if result_env is not None and isinstance(result_env.payload, dict):
            payload = result_env.payload
            if "pnl" in payload:
                metrics.append((f"{key}.pnl", float(payload["pnl"]), {}))
            if "trades" in payload:
                metrics.append((f"{key}.trades", float(payload["trades"]), {}))

    pnl_env = ctx.optional("step_pnl")
    if pnl_env is not None:
        metrics.append(("step_pnl", float(pnl_env.payload), {}))

    return metrics
