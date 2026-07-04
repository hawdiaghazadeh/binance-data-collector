"""Marketplace service — install, enable, disable, update, remove."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from packaging.version import Version

from quant_platform.core.compatibility import CompatibilityChecker
from quant_platform.core.manager import PluginManager
from quant_platform.core.plugin import DisableReason, PluginMetadata, PluginStatus
from quant_platform.core.registry import RegistryError
from quant_platform.marketplace.config_store import PluginConfigStore
from quant_platform.marketplace.pip_runner import MarketplaceError, PipRunner, PipRunnerProtocol
from quant_platform.marketplace.state import InstalledPlugin, InstalledPluginStore
from quant_platform.registries.groups import ALL_REGISTRY_GROUPS


@dataclass(frozen=True)
class InstallResult:
    package: str
    installed: list[InstalledPlugin]


@dataclass(frozen=True)
class UpdateResult:
    group: str
    name: str
    old_version: str
    new_version: str
    changed: bool


@dataclass(frozen=True)
class PluginListing:
    group: str
    metadata: PluginMetadata
    status: PluginStatus
    package: str | None = None


def _snapshot(manager: PluginManager) -> set[tuple[str, str]]:
    snapshot: set[tuple[str, str]] = set()
    for group in ALL_REGISTRY_GROUPS:
        for meta in manager.registry(group).list_plugins():
            snapshot.add((group, meta.name))
    return snapshot


class MarketplaceService:
    def __init__(
        self,
        manager: PluginManager,
        *,
        pip_runner: PipRunnerProtocol | None = None,
        state_store: InstalledPluginStore | None = None,
        config_store: PluginConfigStore | None = None,
    ) -> None:
        self._manager = manager
        self._pip = pip_runner or PipRunner()
        self._state = state_store or InstalledPluginStore(Path(".quant_platform/installed_plugins.yaml"))
        self._config = config_store

    def list_plugins(
        self,
        *,
        group: str | None = None,
        installed_only: bool = False,
    ) -> list[PluginListing]:
        groups = [group] if group else list(ALL_REGISTRY_GROUPS)
        installed = {(item.group, item.name): item.package for item in self._state.load()}
        listings: list[PluginListing] = []
        for registry_group in groups:
            reg = self._manager.registry(registry_group)
            for meta in reg.list_plugins():
                record = reg.get_record(meta.name)
                package = installed.get((registry_group, meta.name))
                if installed_only and package is None:
                    continue
                listings.append(
                    PluginListing(
                        group=registry_group,
                        metadata=meta,
                        status=record.status,
                        package=package,
                    )
                )
        return listings

    def install(self, package: str, *, group: str | None = None) -> InstallResult:
        before = _snapshot(self._manager)
        self._pip.install(package)
        groups = [group] if group else list(ALL_REGISTRY_GROUPS)
        dynamic_modules = [package] if "." in package and not package.startswith(".") else []
        checker = CompatibilityChecker()
        installed: list[InstalledPlugin] = []
        for registry_group in groups:
            self._manager.discover(registry_group, dynamic_modules=dynamic_modules)
            reg = self._manager.registry(registry_group)
            checker.enforce_registry(reg)
            for meta in reg.list_plugins():
                key = (registry_group, meta.name)
                if key in before:
                    continue
                record = reg.get_record(meta.name)
                entry = InstalledPlugin(
                    group=registry_group,
                    name=meta.name,
                    package=package,
                    version=record.metadata.version,
                    installed_at=InstalledPluginStore.now_iso(),
                )
                self._state.add(entry)
                installed.append(entry)
        if not installed:
            raise MarketplaceError(f"No new plugins discovered after installing {package}")
        return InstallResult(package=package, installed=installed)

    def enable(self, group: str, name: str, *, persist: bool = True) -> None:
        reg = self._manager.registry(group)
        reg.get_record(name)
        reg.set_status(name, PluginStatus.ENABLED, disable_reason=None)
        if persist and self._config is not None:
            self._config.enable_plugin(name)

    def disable(self, group: str, name: str, *, persist: bool = True) -> None:
        reg = self._manager.registry(group)
        reg.get_record(name)
        reg.set_status(name, PluginStatus.DISABLED, disable_reason=DisableReason.USER_CONFIG)
        if persist and self._config is not None:
            self._config.disable_plugin(name)

    def update(self, group: str, name: str) -> UpdateResult:
        reg = self._manager.registry(group)
        record = reg.get_record(name)
        old_version = record.metadata.version
        package = self._state.get_package(group, name)
        if package is None:
            raise MarketplaceError(f"No installed package tracked for {group}:{name}")
        self._pip.upgrade(package)
        dynamic_modules = [package] if "." in package and not package.startswith(".") else []
        self._manager.discover(group, dynamic_modules=dynamic_modules)
        CompatibilityChecker().enforce_registry(reg)
        new_record = reg.get_record(name)
        new_version = new_record.metadata.version
        self._state.add(
            InstalledPlugin(
                group=group,
                name=name,
                package=package,
                version=new_version,
                installed_at=InstalledPluginStore.now_iso(),
            )
        )
        return UpdateResult(
            group=group,
            name=name,
            old_version=old_version,
            new_version=new_version,
            changed=Version(new_version) != Version(old_version),
        )

    def remove(self, group: str, name: str, *, uninstall_package: bool = True) -> None:
        reg = self._manager.registry(group)
        reg.get_record(name)
        removed = self._state.remove(group, name)
        reg.unregister(name)
        if uninstall_package and removed is not None:
            self._pip.uninstall(removed.package)

    def find_plugin(self, name: str, *, group: str | None = None) -> tuple[str, Any]:
        groups = [group] if group else list(ALL_REGISTRY_GROUPS)
        for registry_group in groups:
            try:
                return registry_group, self._manager.registry(registry_group).get_record(name)
            except RegistryError:
                continue
        raise MarketplaceError(f"Plugin '{name}' not found")
