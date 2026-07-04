"""Dynamic-import discovery test plugin."""

from __future__ import annotations

from quant_platform.core.context import PipelineContext
from quant_platform.core.plugin import PluginMetadata

PLUGIN_METADATA = PluginMetadata(
    name="dynamic_feature",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Plugin loaded via dynamic import path",
    registry_group="platform.test.g5",
)


class DynamicFeature:
    def compute(self, ctx: PipelineContext) -> None:
        return None


def factory(**kwargs) -> DynamicFeature:
    return DynamicFeature()
