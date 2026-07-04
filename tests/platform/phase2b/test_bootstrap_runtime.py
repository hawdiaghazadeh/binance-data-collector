"""Phase 2B bootstrap runtime integration tests (G2)."""

from __future__ import annotations

from quant_platform.bootstrap import bootstrap_pipeline
from quant_platform.core.context import PipelineContext
from quant_platform.core.manager import PluginManager
from quant_platform.core.plugin import PluginLifecycle, PluginMetadata
from quant_platform.core.registry import BaseRegistry
from quant_platform.registries.pipeline import DATA_PROVIDER_GROUP
from quant_platform.runtime import PipelineRuntime, compile_pipeline_graph
from services.shared.config import AppConfig, PathsConfig, PluginsConfigSection


def _test_config(*, resolve_graph: bool = True) -> AppConfig:
    return AppConfig(
        symbols=["BTCUSDT"],
        timeframes=["1h"],
        paths=PathsConfig(download_dir="./downloads", logs_dir="./logs", state_dir="./downloads/.state"),
        plugins=PluginsConfigSection(resolve_graph=resolve_graph),
    )


class TestPipelineRuntime:
    def test_bootstrap_returns_runtime_with_graph(self):
        runtime = bootstrap_pipeline(_test_config())
        assert isinstance(runtime, PipelineRuntime)
        assert runtime.manager is not None
        assert runtime.data_provider is not None
        assert runtime.storage_backend is not None
        assert runtime.parser is not None
        assert len(runtime.execution_graph) == 3

    def test_execution_graph_zero_registry_lookup(self):
        runtime = bootstrap_pipeline(_test_config())
        ctx = PipelineContext()
        runtime.execution_graph.execute(ctx)
        assert ctx.require("data_provider").payload is runtime.data_provider
        assert ctx.require("storage_backend").payload is runtime.storage_backend
        assert ctx.require("parser").payload is runtime.parser

    def test_singleton_instances_cached_via_manager(self):
        runtime = bootstrap_pipeline(_test_config())
        first = runtime.manager.get(DATA_PROVIDER_GROUP, "binance_vision")
        second = runtime.manager.get(DATA_PROVIDER_GROUP, "binance_vision")
        assert first is second
        assert first is runtime.data_provider

    def test_resolve_graph_can_be_disabled(self):
        runtime = bootstrap_pipeline(_test_config(resolve_graph=False), resolve_graph=False)
        assert runtime.data_provider is not None

    def test_config_without_plugins_section(self):
        config = AppConfig(symbols=["ETHUSDT"], timeframes=["1m"])
        runtime = bootstrap_pipeline(config)
        assert runtime.manager is not None


class TestInstanceManagerIntegration:
    def test_singleton_lifecycle_in_manager(self):
        group = "platform.test.g2"
        reg = BaseRegistry.get_instance(group)
        for meta in reg.list_plugins():
            reg.unregister(meta.name)

        calls: list[int] = []

        def factory():
            calls.append(1)
            return object()

        reg.register(
            PluginMetadata(
                name="singleton_test",
                version="1.0.0",
                platform_version_compatibility=">=1.0.0,<2.0.0",
                lifecycle=PluginLifecycle.SINGLETON,
            ),
            factory,
        )

        manager = PluginManager()
        a = manager.get(group, "singleton_test")
        b = manager.get(group, "singleton_test")
        assert a is b
        assert len(calls) == 1


class TestCompilePipelineGraph:
    def test_compile_closes_over_instances(self):
        sentinel_provider = object()
        sentinel_storage = object()
        sentinel_parser = object()
        graph = compile_pipeline_graph(sentinel_provider, sentinel_storage, sentinel_parser)
        ctx = PipelineContext()
        graph.execute(ctx)
        assert ctx.require("data_provider").payload is sentinel_provider
