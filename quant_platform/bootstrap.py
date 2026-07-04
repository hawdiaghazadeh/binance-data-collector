"""Platform bootstrap and plugin loading helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from quant_platform.core.compatibility import (
    CompatibilityChecker,
    build_compatibility_context,
)
from quant_platform.core.dependencies import DependencyResolver
from quant_platform.core.manager import PluginManager
from quant_platform.core.plugin import DisableReason, PluginStatus
from quant_platform.plugins.binance_kline_parser import PLUGIN_METADATA as PARSER_META
from quant_platform.plugins.binance_kline_parser import BinanceKlineParser
from quant_platform.plugins.binance_kline_parser import factory as parser_factory
from quant_platform.plugins.binance_klines_monthly import PLUGIN_METADATA as BUILDER_META
from quant_platform.plugins.binance_klines_monthly import factory as builder_factory
from quant_platform.plugins.binance_vision import PLUGIN_METADATA as PROVIDER_META
from quant_platform.plugins.binance_vision import BinanceVisionDataProvider
from quant_platform.plugins.binance_vision import factory as provider_factory
from quant_platform.plugins.clickhouse import PLUGIN_METADATA as STORAGE_META
from quant_platform.plugins.clickhouse import ClickHouseStorageBackend
from quant_platform.plugins.clickhouse import factory as storage_factory
from quant_platform.registries.pipeline import (
    DATA_PROVIDER_GROUP,
    DATASET_BUILDER_GROUP,
    PARSER_GROUP,
    STORAGE_BACKEND_GROUP,
)
from quant_platform.runtime import PipelineRuntime, materialize_runtime

if TYPE_CHECKING:
    from services.shared.config import AppConfig

PIPELINE_GROUPS = (
    DATA_PROVIDER_GROUP,
    STORAGE_BACKEND_GROUP,
    PARSER_GROUP,
    DATASET_BUILDER_GROUP,
)


def create_plugin_manager(app_config: AppConfig) -> PluginManager:
    return PluginManager.from_app_config(app_config)


def _resolve_graph_enabled(app_config: AppConfig, override: bool | None) -> bool:
    if override is not None:
        return override
    plugins = getattr(app_config, "plugins", None)
    if plugins is None:
        return True
    return getattr(plugins, "resolve_graph", True)


def register_pipeline_plugins(manager: PluginManager, app_config: AppConfig) -> None:
    """Register built-in pipeline plugins (Phase 2A simple load)."""
    mappings = [
        (DATA_PROVIDER_GROUP, PROVIDER_META, lambda **kw: provider_factory(config=app_config, **kw)),
        (STORAGE_BACKEND_GROUP, STORAGE_META, lambda **kw: storage_factory(config=app_config, **kw)),
        (PARSER_GROUP, PARSER_META, lambda **kw: parser_factory(**kw)),
    ]
    for group, meta, factory in mappings:
        reg = manager.registry(group)
        if meta.name not in {m.name for m in reg.list_plugins()}:
            reg.register(meta, factory)

    reg = manager.registry(DATASET_BUILDER_GROUP)
    if BUILDER_META.name not in {m.name for m in reg.list_plugins()}:
        provider = manager.get(DATA_PROVIDER_GROUP, "binance_vision")
        storage = manager.get(STORAGE_BACKEND_GROUP, "clickhouse")
        parser = manager.get(PARSER_GROUP, "binance_kline_csv")
        reg.register(
            BUILDER_META,
            lambda **kw: builder_factory(
                data_provider=provider, storage=storage, parser=parser, **kw
            ),
        )


def resolve_dependency_graph(manager: PluginManager) -> None:
    """Phase 2B: enforce compatibility and cascade disabled dependents."""
    context = build_compatibility_context(manager)
    checker = CompatibilityChecker(context=context)
    for group in PIPELINE_GROUPS:
        reg = manager.registry(group)
        checker.enforce_registry(reg)
        resolver = DependencyResolver.from_registry(reg)
        changed = resolver.cascade_disabled()
        for name, reason in changed.items():
            reg.set_status(name, PluginStatus.DISABLED, disable_reason=reason)


def load_pipeline_plugins(manager: PluginManager, *, resolve_graph: bool) -> None:
    """Batch-load pipeline plugins in dependency order after optional graph resolution."""
    if resolve_graph:
        resolve_dependency_graph(manager)
    for group in PIPELINE_GROUPS:
        manager.batch_load(group, resolve_graph=resolve_graph)


def bootstrap_pipeline(
    app_config: AppConfig,
    *,
    resolve_graph: bool | None = None,
) -> PipelineRuntime:
    """Discover, register, resolve, and compile the pipeline for runtime execution."""
    graph_enabled = _resolve_graph_enabled(app_config, resolve_graph)
    manager = create_plugin_manager(app_config)
    for group in PIPELINE_GROUPS:
        manager.discover(group)
    register_pipeline_plugins(manager, app_config)
    load_pipeline_plugins(manager, resolve_graph=graph_enabled)
    return materialize_runtime(manager)


def get_data_provider(manager: PluginManager, app_config: AppConfig) -> BinanceVisionDataProvider:
    register_pipeline_plugins(manager, app_config)
    return manager.get(DATA_PROVIDER_GROUP, "binance_vision")


def get_storage_backend(
    manager: PluginManager, app_config: AppConfig
) -> ClickHouseStorageBackend:
    register_pipeline_plugins(manager, app_config)
    return manager.get(STORAGE_BACKEND_GROUP, "clickhouse")


def get_parser(manager: PluginManager) -> BinanceKlineParser:
    return manager.get(PARSER_GROUP, "binance_kline_csv")
