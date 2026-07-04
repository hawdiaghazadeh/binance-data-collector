"""Shared helpers for reference domain plugins."""

from __future__ import annotations

from typing import Any, Callable, TypeVar

from quant_platform.core.plugin import PluginMetadata

DEFAULT_PLATFORM_COMPAT = ">=1.0.0,<2.0.0"
T = TypeVar("T")


def reference_meta(name: str, group: str, description: str = "") -> PluginMetadata:
    return PluginMetadata(
        name=name,
        version="1.0.0",
        platform_version_compatibility=DEFAULT_PLATFORM_COMPAT,
        description=description or f"Reference {name} plugin",
        registry_group=group,
    )


def attach_factory_metadata(factory: Callable[..., T], meta: PluginMetadata) -> Callable[..., T]:
    factory.PLUGIN_METADATA = meta  # type: ignore[attr-defined]
    return factory
