"""Order block market structure plugin (Phase 6)."""

from __future__ import annotations

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.plugin import PluginMetadata
from quant_platform.market_structure.order_blocks import detect_order_blocks
from quant_platform.market_structure.source import resolve_bars

PLUGIN_METADATA = PluginMetadata(
    name="order_blocks",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Detect order blocks before impulsive displacement moves",
    input_types=["klines", "ohlc"],
    output_types=["order_blocks"],
    registry_group="platform.market_structures",
)


class OrderBlockAnalyzer:
    def __init__(self, displacement_pct: float = 0.005) -> None:
        self._displacement_pct = displacement_pct

    def analyze(self, ctx: PipelineContext) -> None:
        bars = resolve_bars(ctx)
        blocks = detect_order_blocks(bars, displacement_pct=self._displacement_pct)
        ctx.emit(
            DataEnvelope(
                type_key="order_blocks",
                payload=blocks,
                metadata={"displacement_pct": self._displacement_pct},
            )
        )


def factory(*, displacement_pct: float = 0.005, config: dict | None = None, **kwargs) -> OrderBlockAnalyzer:
    if config and "displacement_pct" in config:
        displacement_pct = float(config["displacement_pct"])
    return OrderBlockAnalyzer(displacement_pct=displacement_pct)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
