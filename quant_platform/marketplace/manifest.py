"""plugin.yaml manifest loader for marketplace plugins."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator

from quant_platform.core.plugin import PluginLifecycle, PluginMetadata
from quant_platform.marketplace.pip_runner import MarketplaceError


class PluginManifest(BaseModel):
    name: str
    version: str
    registry_group: str
    platform_version_compatibility: str
    package: str
    description: str = ""
    author: str = ""
    license: str = ""
    factory: str = "factory"
    entry_points: dict[str, dict[str, str]] = Field(default_factory=dict)

    @field_validator("version")
    @classmethod
    def validate_semver(cls, value: str) -> str:
        from packaging.version import InvalidVersion, Version

        try:
            Version(value)
        except InvalidVersion as exc:
            raise ValueError(f"Invalid SemVer: {value}") from exc
        return value

    def to_metadata(self, *, name: str | None = None, group: str | None = None) -> PluginMetadata:
        return PluginMetadata(
            name=name or self.name,
            version=self.version,
            platform_version_compatibility=self.platform_version_compatibility,
            author=self.author,
            description=self.description,
            license=self.license,
            lifecycle=PluginLifecycle.TRANSIENT,
            registry_group=group or self.registry_group,
        )

    def groups(self) -> list[str]:
        if self.entry_points:
            return list(self.entry_points.keys())
        return [self.registry_group]

    def targets_for_group(self, group: str) -> dict[str, str]:
        if group in self.entry_points:
            return dict(self.entry_points[group])
        if group == self.registry_group:
            return {self.name: f"{self.package}:{self.factory}"}
        return {}


def load_plugin_manifest(path: str | Path) -> PluginManifest:
    file_path = Path(path)
    if not file_path.exists():
        raise MarketplaceError(f"Plugin manifest not found: {file_path}")
    payload = yaml.safe_load(file_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise MarketplaceError("Plugin manifest root must be an object")
    return PluginManifest.model_validate(payload)


def find_manifest_path(package: str) -> Path | None:
    try:
        module = importlib.import_module(package)
    except Exception:
        return None

    module_paths = getattr(module, "__path__", None)
    if module_paths:
        candidate = Path(module_paths[0]) / "plugin.yaml"
        if candidate.exists():
            return candidate

    module_file = getattr(module, "__file__", None)
    if module_file:
        candidate = Path(module_file).parent / "plugin.yaml"
        if candidate.exists():
            return candidate
    return None


def load_plugin_manifest_from_package(package: str) -> PluginManifest | None:
    manifest_path = find_manifest_path(package)
    if manifest_path is None:
        return None
    manifest = load_plugin_manifest(manifest_path)
    if manifest.package != package:
        raise MarketplaceError(
            f"Manifest package '{manifest.package}' does not match requested package '{package}'"
        )
    return manifest
