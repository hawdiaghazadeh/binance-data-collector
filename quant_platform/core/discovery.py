"""Plugin discovery via entry points and decorators."""

from __future__ import annotations

import importlib.metadata
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from quant_platform.core.plugin import PluginMetadata
from quant_platform.core.registry import BaseRegistry, RegistryError

_PENDING: dict[str, list[tuple[PluginMetadata, Callable[..., Any]]]] = {}


def register(group: str, metadata: PluginMetadata | None = None):
    """Decorator to register a plugin factory with a registry group."""

    def decorator(factory: Callable[..., Any]) -> Callable[..., Any]:
        meta = metadata or getattr(factory, "PLUGIN_METADATA", None)
        if meta is None:
            raise RegistryError(f"Plugin factory {factory.__name__} missing PLUGIN_METADATA")
        _PENDING.setdefault(group, []).append((meta, factory))
        return factory

    return decorator


@dataclass
class DiscoveryConfig:
    groups: list[str] = field(default_factory=list)
    enabled: list[str] | None = None
    disabled: list[str] = field(default_factory=list)


def discover_entry_points(group: str) -> list[tuple[PluginMetadata, Callable[..., Any]]]:
    """Load plugins from setuptools entry points for a group."""
    results: list[tuple[PluginMetadata, Callable[..., Any]]] = []
    try:
        eps = importlib.metadata.entry_points(group=group)
    except TypeError:
        eps = importlib.metadata.entry_points().get(group, [])

    for ep in eps:
        try:
            loaded = ep.load()
            if isinstance(loaded, tuple) and len(loaded) == 2:
                meta, factory = loaded
            elif callable(loaded):
                meta = getattr(loaded, "PLUGIN_METADATA", None)
                factory = loaded
            else:
                meta = getattr(loaded, "PLUGIN_METADATA", None)
                factory = getattr(loaded, "factory", loaded)
            if meta is None:
                continue
            results.append((meta, factory))
        except Exception:
            continue
    return results


def discover_package_plugins(package_path: str, group: str) -> list[tuple[PluginMetadata, Callable[..., Any]]]:
    """Scan a package path for modules exporting PLUGIN_METADATA (Phase 2A)."""
    results: list[tuple[PluginMetadata, Callable[..., Any]]] = []
    try:
        import importlib
        import pkgutil

        pkg = importlib.import_module(package_path)
        for _finder, name, _ispkg in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + "."):
            try:
                mod = importlib.import_module(name)
                meta = getattr(mod, "PLUGIN_METADATA", None)
                factory = getattr(mod, "factory", getattr(mod, "create_plugin", None))
                if meta and factory:
                    results.append((meta, factory))
            except Exception:
                continue
    except Exception:
        pass
    return results


def flush_pending(group: str) -> list[tuple[PluginMetadata, Callable[..., Any]]]:
    """Flush decorator-registered plugins for a group."""
    pending = _PENDING.pop(group, [])
    return pending


def clear_pending() -> None:
    """Clear all pending registrations (for tests)."""
    _PENDING.clear()
