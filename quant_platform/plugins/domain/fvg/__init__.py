"""Fair Value Gap market structure plugin (Phase 6)."""

from __future__ import annotations

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.plugin import PluginMetadata
from quant_platform.market_structure.fvg import detect_fvg
from quant_platform.market_structure.source import resolve_bars

PLUGIN_METADATA = PluginMetadata(
    name="fvg",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Detect three-candle fair value gaps",
    input_types=["klines", "ohlc"],
    output_types=["fvg"],
    registry_group="platform.market_structures",
)


class FvgAnalyzer:
    def analyze(self, ctx: PipelineContext) -> None:
        bars = resolve_bars(ctx)
        gaps = detect_fvg(bars)
        ctx.emit(DataEnvelope(type_key="fvg", payload=gaps))


def factory(**kwargs) -> FvgAnalyzer:
    return FvgAnalyzer()


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
