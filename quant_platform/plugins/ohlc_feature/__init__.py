"""OHLC feature plugin."""

from __future__ import annotations

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.plugin import PluginMetadata

PLUGIN_METADATA = PluginMetadata(
    name="ohlc_feature",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Extract OHLC from kline data",
    input_types=["klines"],
    output_types=["ohlc"],
    registry_group="platform.features",
)


class OhlcFeature:
    def compute(self, ctx: PipelineContext) -> None:
        klines_env = ctx.require("klines")
        rows = klines_env.payload
        ohlc = [
            {
                "open": r.open if hasattr(r, "open") else r.get("open"),
                "high": r.high if hasattr(r, "high") else r.get("high"),
                "low": r.low if hasattr(r, "low") else r.get("low"),
                "close": r.close if hasattr(r, "close") else r.get("close"),
            }
            for r in rows
        ]
        ctx.emit(DataEnvelope(type_key="ohlc", payload=ohlc))


def factory(**kwargs) -> OhlcFeature:
    return OhlcFeature()
