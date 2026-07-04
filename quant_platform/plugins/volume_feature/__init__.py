"""Volume feature plugin."""

from __future__ import annotations

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.plugin import PluginMetadata

PLUGIN_METADATA = PluginMetadata(
    name="volume_feature",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Extract volume from kline data",
    input_types=["klines"],
    output_types=["volume"],
    registry_group="platform.features",
)


class VolumeFeature:
    def compute(self, ctx: PipelineContext) -> None:
        klines_env = ctx.require("klines")
        rows = klines_env.payload
        volumes = [
            r.volume if hasattr(r, "volume") else r.get("volume", 0) for r in rows
        ]
        ctx.emit(DataEnvelope(type_key="volume", payload=volumes))


def factory(**kwargs) -> VolumeFeature:
    return VolumeFeature()
