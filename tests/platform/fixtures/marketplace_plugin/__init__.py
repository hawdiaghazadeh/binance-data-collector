"""Dynamic-import marketplace test plugin."""

from __future__ import annotations

from quant_platform.core.context import PipelineContext
from quant_platform.core.plugin import PluginMetadata

PLUGIN_METADATA = PluginMetadata(
    name="marketplace_feature",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Plugin used by marketplace CLI tests",
    registry_group="platform.test.marketplace",
)


class MarketplaceFeature:
    def compute(self, ctx: PipelineContext) -> None:
        return None


def factory(**kwargs) -> MarketplaceFeature:
    return MarketplaceFeature()
