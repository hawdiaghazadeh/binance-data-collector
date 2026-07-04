"""MACD indicator plugin (Phase 5)."""

from __future__ import annotations

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.plugin import PluginMetadata
from quant_platform.indicators.compute import compute_macd
from quant_platform.indicators.source import resolve_closes

PLUGIN_METADATA = PluginMetadata(
    name="macd_indicator",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="MACD line, signal line, and histogram on close prices",
    input_types=["klines", "ohlc"],
    output_types=["macd"],
    registry_group="platform.indicators",
)


class MacdIndicator:
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9) -> None:
        self._fast = fast
        self._slow = slow
        self._signal = signal

    def compute(self, ctx: PipelineContext) -> None:
        closes = resolve_closes(ctx)
        macd_line, signal_line, histogram = compute_macd(
            closes,
            fast=self._fast,
            slow=self._slow,
            signal=self._signal,
        )
        ctx.emit(
            DataEnvelope(
                type_key="macd",
                payload={
                    "macd": macd_line,
                    "signal": signal_line,
                    "histogram": histogram,
                },
                metadata={
                    "fast": self._fast,
                    "slow": self._slow,
                    "signal": self._signal,
                },
            )
        )


def factory(
    *,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
    config: dict | None = None,
    **kwargs,
) -> MacdIndicator:
    if config:
        fast = int(config.get("fast", fast))
        slow = int(config.get("slow", slow))
        signal = int(config.get("signal", signal))
    return MacdIndicator(fast=fast, slow=slow, signal=signal)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
