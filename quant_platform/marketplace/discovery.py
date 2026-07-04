"""Manifest-driven plugin discovery and entry-point verification."""

from __future__ import annotations

import importlib
import importlib.metadata
from collections.abc import Callable
from typing import Any

from quant_platform.core.compatibility import CompatibilityChecker
from quant_platform.core.discovery import discover_entry_points
from quant_platform.core.manager import PluginManager
from quant_platform.core.plugin import PluginMetadata
from quant_platform.core.registry import BaseRegistry
from quant_platform.marketplace.manifest import PluginManifest


def load_entry_point_target(target: str) -> Callable[..., Any]:
    module_path, attr = target.split(":", 1)
    module = importlib.import_module(module_path)
    loaded = getattr(module, attr)
    if not callable(loaded):
        raise ValueError(f"Entry point target is not callable: {target}")
    return loaded


def _resolve_metadata(
    factory: Callable[..., Any],
    manifest: PluginManifest,
    *,
    name: str,
    group: str,
) -> PluginMetadata:
    meta = getattr(factory, "PLUGIN_METADATA", None)
    if meta is None:
        return manifest.to_metadata(name=name, group=group)
    if meta.registry_group and meta.registry_group != group:
        return meta.model_copy(update={"registry_group": group})
    return meta


def register_plugins_from_manifest(
    manager: PluginManager,
    manifest: PluginManifest,
    *,
    groups: list[str] | None = None,
) -> list[tuple[str, str]]:
    registered: list[tuple[str, str]] = []
    target_groups = groups or manifest.groups()
    checker = CompatibilityChecker()

    for registry_group in target_groups:
        reg = manager.registry(registry_group)
        for name, target in manifest.targets_for_group(registry_group).items():
            if name in {meta.name for meta in reg.list_plugins()}:
                continue
            factory = load_entry_point_target(target)
            meta = _resolve_metadata(factory, manifest, name=name, group=registry_group)
            if not checker.is_compatible(meta):
                reason = checker.incompatibility_reason(meta)
                raise ValueError(reason or f"Plugin {name} is incompatible with the platform")
            manager._safe_register(reg, meta, factory)
            registered.append((registry_group, name))
    return registered


def discover_entry_points_from_manifest(manifest: PluginManifest) -> list[tuple[str, PluginMetadata, Callable[..., Any]]]:
    discovered: list[tuple[str, PluginMetadata, Callable[..., Any]]] = []
    for registry_group in manifest.groups():
        for name, target in manifest.targets_for_group(registry_group).items():
            factory = load_entry_point_target(target)
            meta = _resolve_metadata(factory, manifest, name=name, group=registry_group)
            discovered.append((registry_group, meta, factory))
    return discovered


def verify_manifest_entry_points(manifest: PluginManifest) -> list[str]:
    """Cross-check manifest targets against installed setuptools entry points."""
    mismatches: list[str] = []
    for registry_group, plugins in manifest.entry_points.items():
        try:
            eps = importlib.metadata.entry_points(group=registry_group)
        except TypeError:
            eps = importlib.metadata.entry_points().get(registry_group, [])

        installed = {ep.name: ep.value for ep in eps}
        for name, target in plugins.items():
            if name not in installed:
                mismatches.append(f"Missing pip entry point {registry_group}:{name}")
            elif installed[name] != target:
                mismatches.append(
                    f"Target mismatch for {registry_group}:{name}: "
                    f"manifest={target} pip={installed[name]}"
                )
    return mismatches


def discover_installed_entry_points(
    manager: PluginManager,
    *,
    groups: list[str] | None = None,
) -> list[tuple[str, PluginMetadata]]:
    """Register plugins discovered via setuptools entry points."""
    registered: list[tuple[str, PluginMetadata]] = []
    target_groups = groups or []
    if not target_groups:
        from quant_platform.registries.groups import ALL_REGISTRY_GROUPS

        target_groups = list(ALL_REGISTRY_GROUPS)

    for registry_group in target_groups:
        reg = manager.registry(registry_group)
        for meta, factory in discover_entry_points(registry_group):
            if meta.name in {item.name for item in reg.list_plugins()}:
                continue
            manager._safe_register(reg, meta, factory)
            registered.append((registry_group, meta))
    return registered


def reconcile_manifest_with_entry_points(
    manifest: PluginManifest,
    registry: BaseRegistry[Any],
    *,
    group: str,
) -> list[str]:
    """Ensure manifest-declared plugins are present in the registry."""
    missing: list[str] = []
    for name in manifest.targets_for_group(group):
        if name not in {meta.name for meta in registry.list_plugins()}:
            missing.append(name)
    return missing
