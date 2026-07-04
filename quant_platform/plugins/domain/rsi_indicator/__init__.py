"""RSI indicator plugin (Phase 5)."""

from __future__ import annotations

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.plugin import PluginMetadata
from quant_platform.indicators.compute import compute_rsi
from quant_platform.indicators.source import resolve_closes

PLUGIN_METADATA = PluginMetadata(
    name="rsi_indicator",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Wilder RSI on close prices",
    input_types=["klines", "ohlc"],
    output_types=["rsi"],
    registry_group="platform.indicators",
)


class RsiIndicator:
    def __init__(self, period: int = 14) -> None:
        self._period = period

    def compute(self, ctx: PipelineContext) -> None:
        closes = resolve_closes(ctx)
        rsi = compute_rsi(closes, self._period)
        ctx.emit(
            DataEnvelope(
                type_key="rsi",
                payload=rsi,
                metadata={"period": self._period},
            )
        )


def factory(*, period: int = 14, config: dict | None = None, **kwargs) -> RsiIndicator:
    if config and "period" in config:
        period = int(config["period"])
    return RsiIndicator(period=period)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
