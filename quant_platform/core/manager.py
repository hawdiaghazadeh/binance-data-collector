"""PluginManager — discover, register, load with Safe-Mode."""

from __future__ import annotations

import traceback
from dataclasses import dataclass, field
from typing import Any

from quant_platform.core.config import ConfigValidationError, validate_plugin_config
from quant_platform.core.discovery import DEFAULT_SCAN_PACKAGES, iter_discovery_sources
from quant_platform.core.instances import InstanceManager
from quant_platform.core.plugin import DisableReason, PluginLifecycle, PluginMetadata, PluginStatus
from quant_platform.core.registry import BaseRegistry, PluginUnavailableError, RegistryError


@dataclass
class PluginsConfig:
    safe_mode: bool = True
    fail_fast: bool = False
    enabled: list[str] | None = None
    disabled: list[str] = field(default_factory=list)
    scan_packages: list[str] = field(default_factory=lambda: list(DEFAULT_SCAN_PACKAGES))
    dynamic_modules: list[str] = field(default_factory=list)
    reflection_modules: list[str] = field(default_factory=list)


class PluginManager:
    """Central plugin lifecycle manager."""

    def __init__(
        self,
        *,
        plugins_config: PluginsConfig | None = None,
        plugin_configs: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self._plugins_config = plugins_config or PluginsConfig()
        self._plugin_configs = plugin_configs or {}
        self._registries: dict[str, BaseRegistry[Any]] = {}
        self._instances = InstanceManager()

    @property
    def instances(self) -> InstanceManager:
        return self._instances

    def shutdown(self) -> None:
        self._instances.shutdown()

    def registry(self, group: str) -> BaseRegistry[Any]:
        if group not in self._registries:
            self._registries[group] = BaseRegistry.get_instance(group)
        return self._registries[group]

    def discover(
        self,
        group: str,
        *,
        scan_packages: list[str] | None = None,
        dynamic_modules: list[str] | None = None,
        reflection_modules: list[str] | None = None,
    ) -> int:
        """Discover and register plugins for a group. Returns count registered."""
        reg = self.registry(group)
        count = 0
        packages = scan_packages if scan_packages is not None else self._plugins_config.scan_packages
        dynamic = dynamic_modules if dynamic_modules is not None else self._plugins_config.dynamic_modules
        reflection = (
            reflection_modules if reflection_modules is not None else self._plugins_config.reflection_modules
        )

        for meta, factory in iter_discovery_sources(
            group,
            scan_packages=packages,
            dynamic_modules=dynamic,
            reflection_modules=reflection,
        ):
            if meta.name in {m.name for m in reg.list_plugins()}:
                continue
            if self._should_register(meta.name):
                self._safe_register(reg, meta, factory)
                count += 1

        return count

    def _should_register(self, name: str) -> bool:
        cfg = self._plugins_config
        if name in cfg.disabled:
            return True
        if cfg.enabled is not None:
            return name in cfg.enabled
        return True

    def _safe_register(
        self,
        reg: BaseRegistry[Any],
        meta: PluginMetadata,
        factory: Any,
    ) -> None:
        status = meta.status
        disable_reason = None

        if meta.name in self._plugins_config.disabled:
            status = PluginStatus.DISABLED
            disable_reason = DisableReason.USER_CONFIG
        elif (
            self._plugins_config.enabled is not None
            and meta.name not in self._plugins_config.enabled
        ):
            status = PluginStatus.DISABLED
            disable_reason = DisableReason.USER_CONFIG

        try:
            reg.register(meta, factory, status=status, disable_reason=disable_reason)
        except RegistryError:
            if not self._plugins_config.safe_mode:
                raise

    def get(
        self,
        group: str,
        name: str,
        *,
        config: dict[str, Any] | None = None,
        run_id: str | None = None,
    ) -> Any:
        reg = self.registry(group)
        record = reg.get_record(name)

        if record.status != PluginStatus.ENABLED:
            raise PluginUnavailableError(name, record.disable_reason)

        merged_config = {**self._plugin_configs.get(name, {}), **(config or {})}
        if record.metadata.config_schema and merged_config:
            try:
                validate_plugin_config(merged_config, record.metadata.config_schema)
            except ConfigValidationError as exc:
                if self._plugins_config.safe_mode:
                    reg.set_status(
                        name,
                        PluginStatus.DISABLED,
                        disable_reason=DisableReason.LOAD_CRASH,
                        last_error=str(exc),
                    )
                    raise PluginUnavailableError(name, DisableReason.LOAD_CRASH, str(exc)) from exc
                raise

        lifecycle = record.metadata.lifecycle
        cache_key = f"{group}:{name}"

        def instantiate() -> Any:
            return reg.get(name, config=merged_config if merged_config else None)

        if self._plugins_config.safe_mode:
            try:
                instance = self._resolve_instance(
                    cache_key,
                    lifecycle,
                    instantiate,
                    run_id=run_id,
                )
                reg.mark_loaded(name)
                return instance
            except PluginUnavailableError:
                raise
            except Exception as exc:
                reg.set_status(
                    name,
                    PluginStatus.DISABLED,
                    disable_reason=DisableReason.LOAD_CRASH,
                    last_error=f"{exc}\n{traceback.format_exc()}",
                )
                raise PluginUnavailableError(name, DisableReason.LOAD_CRASH, str(exc)) from exc

        instance = self._resolve_instance(
            cache_key,
            lifecycle,
            instantiate,
            run_id=run_id,
        )
        reg.mark_loaded(name)
        return instance

    def _resolve_instance(
        self,
        cache_key: str,
        lifecycle: PluginLifecycle,
        factory: Any,
        *,
        run_id: str | None = None,
    ) -> Any:
        if lifecycle == PluginLifecycle.TRANSIENT:
            return factory()
        return self._instances.get_or_create(
            cache_key,
            lifecycle,
            factory,
            run_id=run_id,
        )

    def list_plugins(self, group: str, *, enabled_only: bool = False) -> list[PluginMetadata]:
        return self.registry(group).list_plugins(enabled_only=enabled_only)

    def batch_load(self, group: str, *, resolve_graph: bool = True) -> list[str]:
        """Phase 2B: load plugins in dependency order after compatibility checks."""
        from quant_platform.core.compatibility import CompatibilityChecker
        from quant_platform.core.dependencies import DependencyResolver
        from quant_platform.core.plugin import PluginStatus

        reg = self.registry(group)
        checker = CompatibilityChecker()
        checker.enforce_registry(reg)
        resolver = DependencyResolver.from_registry(reg)
        load_order = resolver.topological_sort()
        loaded: list[str] = []

        for name in load_order:
            node = resolver.get_node(name)
            if node and node.status != PluginStatus.ENABLED:
                continue
            try:
                self.get(group, name)
                loaded.append(name)
            except Exception:
                if not self._plugins_config.safe_mode:
                    raise
                if resolve_graph:
                    resolver.cascade_disabled()
                    for dep_name, reason in resolver.cascade_disabled().items():
                        reg.set_status(dep_name, PluginStatus.DISABLED, disable_reason=reason)
        return loaded

    @classmethod
    def from_app_config(cls, app_config: Any) -> PluginManager:
        """Build PluginManager from AppConfig (optional plugins section)."""
        plugins_section = getattr(app_config, "plugins", None)
        if plugins_section is None:
            return cls()
        return cls(
            plugins_config=PluginsConfig(
                safe_mode=getattr(plugins_section, "safe_mode", True),
                fail_fast=getattr(plugins_section, "fail_fast", False),
                enabled=getattr(plugins_section, "enabled", None),
                disabled=getattr(plugins_section, "disabled", []) or [],
                scan_packages=getattr(plugins_section, "scan_packages", None)
                or list(DEFAULT_SCAN_PACKAGES),
                dynamic_modules=getattr(plugins_section, "dynamic_modules", []) or [],
                reflection_modules=getattr(plugins_section, "reflection_modules", []) or [],
            ),
        )
