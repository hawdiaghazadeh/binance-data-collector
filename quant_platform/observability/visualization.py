"""Equity curve visualization helpers (Phase 20)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import PipelineContext


def render_equity_curve(ctx: PipelineContext) -> dict[str, Any]:
    equity_env = ctx.optional("equity_curve")
    series = list(equity_env.payload) if equity_env is not None and isinstance(equity_env.payload, list) else []

    points = [{"index": index, "value": float(value)} for index, value in enumerate(series)]
    return {
        "type": "equity_curve",
        "series": [{"name": "equity", "values": series, "points": points}],
        "grafana_panel": {
            "type": "timeseries",
            "title": "Equity Curve",
            "targets": [{"refId": "A", "expr": "equity.latest"}],
        },
    }
