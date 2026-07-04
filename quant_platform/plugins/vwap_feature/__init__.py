"""VWAP (Volume Weighted Average Price) feature plugin."""

from __future__ import annotations

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.plugin import PluginMetadata

PLUGIN_METADATA = PluginMetadata(
    name="vwap_feature",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Cumulative VWAP from kline OHLCV",
    input_types=["klines"],
    output_types=["vwap"],
    registry_group="platform.features",
)


def _row_value(row: object, field: str) -> float:
    if hasattr(row, field):
        return float(getattr(row, field))
    if isinstance(row, dict):
        return float(row[field])
    raise TypeError(f"Unsupported kline row type: {type(row)!r}")


def compute_cumulative_vwap(rows: list[object]) -> list[float]:
    """Compute session-cumulative VWAP using typical price (H+L+C)/3."""
    cumulative_pv = 0.0
    cumulative_volume = 0.0
    values: list[float] = []
    for row in rows:
        typical_price = (
            _row_value(row, "high") + _row_value(row, "low") + _row_value(row, "close")
        ) / 3.0
        volume = _row_value(row, "volume")
        cumulative_pv += typical_price * volume
        cumulative_volume += volume
        values.append(typical_price if cumulative_volume == 0 else cumulative_pv / cumulative_volume)
    return values


class VwapFeature:
    def compute(self, ctx: PipelineContext) -> None:
        klines_env = ctx.require("klines")
        rows = klines_env.payload
        vwap = compute_cumulative_vwap(list(rows))
        ctx.emit(DataEnvelope(type_key="vwap", payload=vwap))


def factory(**kwargs) -> VwapFeature:
    return VwapFeature()
