"""Crash test plugin for Safe-Mode tests."""

from __future__ import annotations

from quant_platform.core.plugin import PluginDependency, PluginMetadata

PLUGIN_METADATA = PluginMetadata(
    name="crash_plugin",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Test plugin that crashes on init",
    registry_group="platform.test",
)


class CrashPlugin:
    def __init__(self) -> None:
        raise RuntimeError("Simulated crash")


def factory(**kwargs) -> CrashPlugin:
    return CrashPlugin()
