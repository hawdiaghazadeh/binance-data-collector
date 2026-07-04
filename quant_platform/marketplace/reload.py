"""Hot-reload config and rebuild compiled execution graphs (Phase 22 / G29)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from quant_platform.bootstrap import (
    PIPELINE_GROUPS,
    load_pipeline_plugins,
    resolve_dependency_graph,
)
from quant_platform.bootstrap import _resolve_graph_enabled
from quant_platform.core.manager import PluginManager
from quant_platform.core.plugin import DisableReason, PluginStatus
from quant_platform.core.registry import BaseRegistry
from quant_platform.registries.groups import ALL_REGISTRY_GROUPS
from quant_platform.runtime import PipelineRuntime, materialize_runtime
from services.shared.config import AppConfig, load_config


@dataclass(frozen=True)
class ReloadResult:
    config_path: Path
    plugins_enabled: int
    plugins_disabled: int
    graph_steps: int


def _iter_registry_groups(manager: PluginManager) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for group in (*PIPELINE_GROUPS, *ALL_REGISTRY_GROUPS, *manager._registries, *BaseRegistry._instances):
        if group not in seen:
            seen.add(group)
            ordered.append(group)
    return ordered


def sync_plugin_status_from_config(manager: PluginManager, app_config: AppConfig) -> tuple[int, int]:
    plugins = getattr(app_config, "plugins", None)
    if plugins is None:
        return 0, 0

    disabled_names = set(getattr(plugins, "disabled", []) or [])
    enabled_names = getattr(plugins, "enabled", None)
    enabled_count = 0
    disabled_count = 0

    for group in _iter_registry_groups(manager):
        reg = manager.registry(group)
        for meta in reg.list_plugins():
            record = reg.get_record(meta.name)
            should_disable = meta.name in disabled_names or (
                enabled_names is not None and meta.name not in enabled_names
            )
            if should_disable:
                if record.status != PluginStatus.DISABLED or record.disable_reason != DisableReason.USER_CONFIG:
                    reg.set_status(meta.name, PluginStatus.DISABLED, disable_reason=DisableReason.USER_CONFIG)
                    disabled_count += 1
                continue

            if record.disable_reason == DisableReason.USER_CONFIG:
                reg.set_status(meta.name, PluginStatus.ENABLED, disable_reason=None)
                enabled_count += 1

    return enabled_count, disabled_count


def reload_pipeline_runtime(
    runtime: PipelineRuntime,
    app_config: AppConfig,
) -> tuple[PipelineRuntime, tuple[int, int]]:
    manager = runtime.manager
    runtime.shutdown()
    counts = sync_plugin_status_from_config(manager, app_config)
    resolve_dependency_graph(manager)
    graph_enabled = _resolve_graph_enabled(app_config, None)
    load_pipeline_plugins(manager, resolve_graph=graph_enabled)
    return materialize_runtime(manager), counts


def reload_from_config_path(
    config_path: Path,
    *,
    runtime: PipelineRuntime | None = None,
) -> tuple[PipelineRuntime, ReloadResult]:
    app_config = load_config(config_path)
    if runtime is None:
        from quant_platform.bootstrap import bootstrap_pipeline

        rebuilt = bootstrap_pipeline(app_config)
        enabled, disabled = 0, 0
    else:
        rebuilt, (enabled, disabled) = reload_pipeline_runtime(runtime, app_config)

    return rebuilt, ReloadResult(
        config_path=config_path,
        plugins_enabled=enabled,
        plugins_disabled=disabled,
        graph_steps=len(rebuilt.execution_graph),
    )
