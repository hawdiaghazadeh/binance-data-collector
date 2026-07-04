"""ATR (Average True Range) feature plugin."""

from __future__ import annotations

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.plugin import PluginMetadata

PLUGIN_METADATA = PluginMetadata(
    name="atr_feature",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Wilder ATR from kline high/low/close",
    input_types=["klines"],
    output_types=["atr"],
    registry_group="platform.features",
)


def _row_value(row: object, field: str) -> float:
    if hasattr(row, field):
        return float(getattr(row, field))
    if isinstance(row, dict):
        return float(row[field])
    raise TypeError(f"Unsupported kline row type: {type(row)!r}")


def compute_wilder_atr(rows: list[object], period: int) -> list[float | None]:
    """Compute Wilder-smoothed ATR aligned with input rows."""
    if period < 1:
        raise ValueError("period must be >= 1")
    if not rows:
        return []

    true_ranges: list[float] = []
    for index, row in enumerate(rows):
        high = _row_value(row, "high")
        low = _row_value(row, "low")
        if index == 0:
            true_ranges.append(high - low)
            continue
        prev_close = _row_value(rows[index - 1], "close")
        true_ranges.append(max(high - low, abs(high - prev_close), abs(low - prev_close)))

    atr_values: list[float | None] = [None] * len(rows)
    if len(rows) < period:
        return atr_values

    first_atr = sum(true_ranges[:period]) / period
    atr_values[period - 1] = first_atr
    prev_atr = first_atr
    for index in range(period, len(rows)):
        prev_atr = (prev_atr * (period - 1) + true_ranges[index]) / period
        atr_values[index] = prev_atr
    return atr_values


class AtrFeature:
    def __init__(self, period: int = 14) -> None:
        self._period = period

    def compute(self, ctx: PipelineContext) -> None:
        klines_env = ctx.require("klines")
        rows = klines_env.payload
        atr = compute_wilder_atr(list(rows), self._period)
        ctx.emit(DataEnvelope(type_key="atr", payload=atr))


def factory(*, period: int = 14, config: dict | None = None, **kwargs) -> AtrFeature:
    if config and "period" in config:
        period = int(config["period"])
    return AtrFeature(period=period)
