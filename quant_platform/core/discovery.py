"""Plugin discovery via entry points and decorators."""

from __future__ import annotations

import importlib
import importlib.metadata
import inspect
import pkgutil
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Any

from quant_platform.core.plugin import PluginMetadata
from quant_platform.core.registry import BaseRegistry, RegistryError

_PENDING: dict[str, list[tuple[PluginMetadata, Callable[..., Any]]]] = {}
DEFAULT_SCAN_PACKAGES = ("quant_platform.plugins",)


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
    scan_packages: list[str] = field(default_factory=lambda: list(DEFAULT_SCAN_PACKAGES))
    dynamic_modules: list[str] = field(default_factory=list)
    reflection_modules: list[str] = field(default_factory=list)


def _matches_group(meta: PluginMetadata, group: str) -> bool:
    return not meta.registry_group or meta.registry_group == group


def _module_level_plugin(
    module: Any,
    group: str,
) -> tuple[PluginMetadata, Callable[..., Any]] | None:
    meta = getattr(module, "PLUGIN_METADATA", None)
    factory = getattr(module, "factory", getattr(module, "create_plugin", None))
    if meta and factory and _matches_group(meta, group):
        return meta, factory
    return None


def _class_level_plugins(
    module: Any,
    group: str,
) -> list[tuple[PluginMetadata, Callable[..., Any]]]:
    results: list[tuple[PluginMetadata, Callable[..., Any]]] = []
    for _, obj in inspect.getmembers(module, inspect.isclass):
        if obj.__module__ != module.__name__:
            continue
        meta = getattr(obj, "PLUGIN_METADATA", None)
        if meta is None or not _matches_group(meta, group):
            continue
        class_factory = getattr(obj, "factory", None)
        if callable(class_factory):
            results.append((meta, class_factory))
        else:
            results.append((meta, lambda cls=obj: cls()))
    return results


def _resolve_plugin_from_loaded(
    loaded: Any,
) -> tuple[PluginMetadata | None, Callable[..., Any] | None]:
    if isinstance(loaded, tuple) and len(loaded) == 2:
        meta, factory = loaded
        return meta, factory

    if callable(loaded):
        meta = getattr(loaded, "PLUGIN_METADATA", None)
        factory = loaded
        if meta is None and getattr(loaded, "__module__", None):
            module = importlib.import_module(loaded.__module__)
            meta = getattr(module, "PLUGIN_METADATA", None)
        return meta, factory

    meta = getattr(loaded, "PLUGIN_METADATA", None)
    factory = getattr(loaded, "factory", loaded)
    return meta, factory


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
            meta, factory = _resolve_plugin_from_loaded(loaded)
            if meta is None or factory is None or not _matches_group(meta, group):
                continue
            results.append((meta, factory))
        except Exception:
            continue
    return results


def discover_package_plugins(
    package_path: str,
    group: str,
) -> list[tuple[PluginMetadata, Callable[..., Any]]]:
    """Scan a package path for modules exporting PLUGIN_METADATA (Phase 2A)."""
    results: list[tuple[PluginMetadata, Callable[..., Any]]] = []
    try:
        pkg = importlib.import_module(package_path)
        pkg_path = getattr(pkg, "__path__", None)
        if pkg_path is None:
            plugin = _module_level_plugin(pkg, group)
            if plugin:
                results.append(plugin)
            return results

        for _finder, name, _ispkg in pkgutil.iter_modules(pkg_path, pkg.__name__ + "."):
            try:
                mod = importlib.import_module(name)
                plugin = _module_level_plugin(mod, group)
                if plugin:
                    results.append(plugin)
            except Exception:
                continue
    except Exception:
        pass
    return results


def discover_dynamic_import(
    module_path: str,
    group: str,
) -> list[tuple[PluginMetadata, Callable[..., Any]]]:
    """Load a plugin from an explicit module path (Phase 5+)."""
    try:
        mod = importlib.import_module(module_path)
    except Exception:
        return []
    plugin = _module_level_plugin(mod, group)
    return [plugin] if plugin else []


def discover_reflection_plugins(
    module_path: str,
    group: str,
) -> list[tuple[PluginMetadata, Callable[..., Any]]]:
    """Scan a module for plugin classes exposing PLUGIN_METADATA (Phase 10+)."""
    try:
        mod = importlib.import_module(module_path)
    except Exception:
        return []
    return _class_level_plugins(mod, group)


def iter_discovery_sources(
    group: str,
    *,
    scan_packages: list[str] | None = None,
    dynamic_modules: list[str] | None = None,
    reflection_modules: list[str] | None = None,
) -> Iterator[tuple[PluginMetadata, Callable[..., Any]]]:
    """Yield plugins from all configured discovery mechanisms (startup only)."""
    for meta, factory in discover_entry_points(group):
        yield meta, factory

    for meta, factory in flush_pending(group):
        yield meta, factory

    for package_path in scan_packages or []:
        for meta, factory in discover_package_plugins(package_path, group):
            yield meta, factory

    for module_path in dynamic_modules or []:
        for meta, factory in discover_dynamic_import(module_path, group):
            yield meta, factory

    for module_path in reflection_modules or []:
        for meta, factory in discover_reflection_plugins(module_path, group):
            yield meta, factory


def flush_pending(group: str) -> list[tuple[PluginMetadata, Callable[..., Any]]]:
    """Flush decorator-registered plugins for a group."""
    pending = _PENDING.pop(group, [])
    return pending


def clear_pending() -> None:
    """Clear all pending registrations (for tests)."""
    _PENDING.clear()
