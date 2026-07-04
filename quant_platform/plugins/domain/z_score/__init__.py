"""Z-score normalizer plugin (Phase 4)."""

from __future__ import annotations

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.plugin import PluginMetadata
from quant_platform.normalizations.z_score import compute_z_score, extract_numeric_series

PLUGIN_METADATA = PluginMetadata(
    name="z_score",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Rolling z-score normalization on a numeric kline field",
    input_types=["klines"],
    output_types=["z_score"],
    registry_group="platform.normalizations",
)


class ZScoreNormalizer:
    def __init__(self, field: str = "close", window: int | None = 20) -> None:
        self._field = field
        self._window = window

    def normalize(self, ctx: PipelineContext) -> None:
        klines_env = ctx.require("klines")
        rows = list(klines_env.payload)
        values = extract_numeric_series(rows, self._field)
        z_scores = compute_z_score(values, window=self._window)
        ctx.emit(
            DataEnvelope(
                type_key="z_score",
                payload=z_scores,
                metadata={"field": self._field, "window": self._window},
            )
        )


def factory(*, field: str = "close", window: int | None = 20, config: dict | None = None, **kwargs) -> ZScoreNormalizer:
    if config:
        field = str(config.get("field", field))
        if "window" in config:
            raw_window = config["window"]
            window = None if raw_window is None else int(raw_window)
    return ZScoreNormalizer(field=field, window=window)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
