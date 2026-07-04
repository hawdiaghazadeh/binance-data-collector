"""Dependent crash test plugin for Phase 2B cascade tests."""

from __future__ import annotations

from quant_platform.core.plugin import PluginDependency, PluginMetadata

PLUGIN_METADATA = PluginMetadata(
    name="crash_plugin_dependent",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Depends on crash_plugin",
    dependencies=[PluginDependency(name="crash_plugin", version="*")],
    registry_group="platform.test",
)


class DependentPlugin:
    def __init__(self) -> None:
        self.ok = True


def factory(**kwargs) -> DependentPlugin:
    return DependentPlugin()
