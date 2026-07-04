"""Direction label plugin (Phase 7)."""

from __future__ import annotations

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.plugin import PluginMetadata
from quant_platform.labels.direction import compute_direction_labels
from quant_platform.labels.source import resolve_label_closes

PLUGIN_METADATA = PluginMetadata(
    name="direction_label",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Supervised direction labels from future close movement",
    input_types=["klines", "ohlc"],
    output_types=["direction_labels"],
    registry_group="platform.labels",
)


class DirectionLabel:
    def __init__(self, horizon: int = 1, threshold_pct: float = 0.0) -> None:
        self._horizon = horizon
        self._threshold_pct = threshold_pct

    def generate(self, ctx: PipelineContext) -> None:
        closes = resolve_label_closes(ctx)
        labels = compute_direction_labels(
            closes,
            horizon=self._horizon,
            threshold_pct=self._threshold_pct,
        )
        ctx.emit(
            DataEnvelope(
                type_key="direction_labels",
                payload=labels,
                metadata={"horizon": self._horizon, "threshold_pct": self._threshold_pct},
            )
        )


def factory(
    *,
    horizon: int = 1,
    threshold_pct: float = 0.0,
    config: dict | None = None,
    **kwargs,
) -> DirectionLabel:
    if config:
        horizon = int(config.get("horizon", horizon))
        threshold_pct = float(config.get("threshold_pct", threshold_pct))
    return DirectionLabel(horizon=horizon, threshold_pct=threshold_pct)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
