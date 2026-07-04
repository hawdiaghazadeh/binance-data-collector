"""Regime label plugin (Phase 7)."""

from __future__ import annotations

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.plugin import PluginMetadata
from quant_platform.labels.regime import compute_regime_labels
from quant_platform.labels.source import resolve_label_closes

PLUGIN_METADATA = PluginMetadata(
    name="regime_label",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Rolling market regime labels: trending, ranging, high volatility",
    input_types=["klines", "ohlc"],
    output_types=["regime_labels"],
    registry_group="platform.labels",
)


class RegimeLabel:
    def __init__(
        self,
        window: int = 20,
        trend_threshold: float = 0.02,
        volatility_threshold: float = 0.01,
    ) -> None:
        self._window = window
        self._trend_threshold = trend_threshold
        self._volatility_threshold = volatility_threshold

    def generate(self, ctx: PipelineContext) -> None:
        closes = resolve_label_closes(ctx)
        labels = compute_regime_labels(
            closes,
            window=self._window,
            trend_threshold=self._trend_threshold,
            volatility_threshold=self._volatility_threshold,
        )
        ctx.emit(
            DataEnvelope(
                type_key="regime_labels",
                payload=labels,
                metadata={
                    "window": self._window,
                    "trend_threshold": self._trend_threshold,
                    "volatility_threshold": self._volatility_threshold,
                },
            )
        )


def factory(
    *,
    window: int = 20,
    trend_threshold: float = 0.02,
    volatility_threshold: float = 0.01,
    config: dict | None = None,
    **kwargs,
) -> RegimeLabel:
    if config:
        window = int(config.get("window", window))
        trend_threshold = float(config.get("trend_threshold", trend_threshold))
        volatility_threshold = float(config.get("volatility_threshold", volatility_threshold))
    return RegimeLabel(
        window=window,
        trend_threshold=trend_threshold,
        volatility_threshold=volatility_threshold,
    )


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
