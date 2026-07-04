"""Platform version compatibility checks (Phase 2B)."""

from __future__ import annotations

from packaging.specifiers import SpecifierSet
from packaging.version import Version

from quant_platform.core.plugin import DisableReason, PluginMetadata, PluginStatus
from quant_platform.core.registry import BaseRegistry
from quant_platform.version import PLATFORM_VERSION


class CompatibilityChecker:
    """Check plugin compatibility with platform version."""

    def __init__(self, platform_version: str = PLATFORM_VERSION) -> None:
        self._platform_version = Version(platform_version)

    def is_compatible(self, metadata: PluginMetadata) -> bool:
        spec = SpecifierSet(metadata.platform_version_compatibility)
        return self._platform_version in spec

    def enforce_registry(self, registry: BaseRegistry) -> list[str]:
        """Disable incompatible plugins; return list of disabled names."""
        disabled: list[str] = []
        for meta in registry.list_plugins():
            if not self.is_compatible(meta):
                registry.set_status(
                    meta.name,
                    PluginStatus.DISABLED,
                    disable_reason=DisableReason.INCOMPATIBLE_VERSION,
                    last_error=(
                        f"Platform {self._platform_version} not in "
                        f"{meta.platform_version_compatibility}"
                    ),
                )
                disabled.append(meta.name)
        return disabled
