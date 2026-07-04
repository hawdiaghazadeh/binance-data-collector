"""Platform and cross-version compatibility checks (Phase 2B / G6)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from packaging.specifiers import SpecifierSet
from packaging.version import Version

from quant_platform.core.plugin import DisableReason, PluginMetadata, PluginStatus
from quant_platform.core.registry import BaseRegistry
from quant_platform.version import PLATFORM_VERSION

if TYPE_CHECKING:
    from quant_platform.core.manager import PluginManager


@dataclass(frozen=True)
class CompatibilityContext:
    """Active ecosystem versions used for cross-version matrix checks."""

    dataset_version: str | None = None
    feature_versions: dict[str, str] = field(default_factory=dict)


def version_matches_spec(version: str, specifier: str) -> bool:
    return Version(version) in SpecifierSet(specifier)


class CompatibilityChecker:
    """Check plugin compatibility with platform and cross-version matrix."""

    def __init__(
        self,
        platform_version: str = PLATFORM_VERSION,
        *,
        context: CompatibilityContext | None = None,
    ) -> None:
        self._platform_version = Version(platform_version)
        self._context = context or CompatibilityContext()

    @property
    def context(self) -> CompatibilityContext:
        return self._context

    def is_platform_compatible(self, metadata: PluginMetadata) -> bool:
        spec = SpecifierSet(metadata.platform_version_compatibility)
        return self._platform_version in spec

    def is_dataset_compatible(self, metadata: PluginMetadata) -> bool:
        spec = metadata.compatible_dataset_versions
        if not spec:
            return True
        dataset_version = self._context.dataset_version
        if dataset_version is None:
            return True
        return version_matches_spec(dataset_version, spec)

    def is_feature_compatible(self, metadata: PluginMetadata) -> bool:
        spec = metadata.compatible_feature_versions
        if not spec:
            return True
        active = self._context.feature_versions
        if not active:
            return True
        return all(version_matches_spec(version, spec) for version in active.values())

    def is_compatible(self, metadata: PluginMetadata) -> bool:
        return (
            self.is_platform_compatible(metadata)
            and self.is_dataset_compatible(metadata)
            and self.is_feature_compatible(metadata)
        )

    def incompatibility_reason(self, metadata: PluginMetadata) -> str | None:
        if not self.is_platform_compatible(metadata):
            return (
                f"Platform {self._platform_version} not in "
                f"{metadata.platform_version_compatibility}"
            )
        if not self.is_dataset_compatible(metadata):
            return (
                f"Dataset {self._context.dataset_version} not in "
                f"{metadata.compatible_dataset_versions}"
            )
        if not self.is_feature_compatible(metadata):
            mismatched = {
                name: version
                for name, version in self._context.feature_versions.items()
                if metadata.compatible_feature_versions
                and not version_matches_spec(version, metadata.compatible_feature_versions)
            }
            return (
                f"Feature versions {mismatched} not in "
                f"{metadata.compatible_feature_versions}"
            )
        return None

    def enforce_registry(self, registry: BaseRegistry) -> list[str]:
        """Disable incompatible plugins; return list of disabled names."""
        disabled: list[str] = []
        for meta in registry.list_plugins():
            reason = self.incompatibility_reason(meta)
            if reason is None:
                continue
            registry.set_status(
                meta.name,
                PluginStatus.DISABLED,
                disable_reason=DisableReason.INCOMPATIBLE_VERSION,
                last_error=reason,
            )
            disabled.append(meta.name)
        return disabled


def build_compatibility_context(manager: PluginManager) -> CompatibilityContext:
    """Collect active dataset and feature versions from a plugin manager."""
    from quant_platform.core.plugin import PluginStatus
    from quant_platform.registries.feature import FEATURE_GROUP
    from quant_platform.registries.pipeline import DATASET_BUILDER_GROUP

    dataset_version: str | None = None
    dataset_registry = manager.registry(DATASET_BUILDER_GROUP)
    for meta in dataset_registry.list_plugins():
        record = dataset_registry.get_record(meta.name)
        if record.status == PluginStatus.ENABLED:
            dataset_version = meta.version
            break

    feature_versions: dict[str, str] = {}
    feature_registry = manager.registry(FEATURE_GROUP)
    for meta in feature_registry.list_plugins():
        record = feature_registry.get_record(meta.name)
        if record.status == PluginStatus.ENABLED:
            feature_versions[meta.name] = meta.version

    return CompatibilityContext(
        dataset_version=dataset_version,
        feature_versions=feature_versions,
    )
