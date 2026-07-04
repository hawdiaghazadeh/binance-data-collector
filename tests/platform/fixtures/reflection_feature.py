"""Reflection discovery test plugin."""

from __future__ import annotations

from quant_platform.core.context import PipelineContext
from quant_platform.core.plugin import PluginMetadata


class ReflectionFeaturePlugin:
    PLUGIN_METADATA = PluginMetadata(
        name="reflection_feature",
        version="1.0.0",
        platform_version_compatibility=">=1.0.0,<2.0.0",
        description="Plugin discovered via class reflection",
        registry_group="platform.test.g5",
    )

    def compute(self, ctx: PipelineContext) -> None:
        return None
