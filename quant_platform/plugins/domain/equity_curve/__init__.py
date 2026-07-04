"""Equity curve visualization plugin (Phase 20)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.plugin import PluginMetadata
from quant_platform.observability.visualization import render_equity_curve

PLUGIN_METADATA = PluginMetadata(
    name="equity_curve",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Grafana-compatible equity curve panel from pipeline context",
    input_types=["equity_curve", "backtest_result", "paper_trading_result"],
    output_types=["visualization"],
    registry_group="platform.visualizations",
)


class EquityCurveViz:
    def render(self, ctx: PipelineContext) -> dict[str, Any]:
        chart = render_equity_curve(ctx)
        ctx.emit(DataEnvelope(type_key="visualization", payload=chart))
        return chart


def factory(**kwargs) -> EquityCurveViz:
    return EquityCurveViz()


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
