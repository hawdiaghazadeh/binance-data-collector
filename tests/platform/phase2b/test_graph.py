"""Phase 2B dependency graph and execution tests."""

from __future__ import annotations

import pytest

from quant_platform.core.compatibility import CompatibilityChecker
from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.dependencies import DependencyResolver
from quant_platform.core.execution_graph import CompiledExecutionGraph, ExecutionStep
from quant_platform.core.instances import InstanceManager
from quant_platform.core.manager import PluginManager, PluginsConfig
from quant_platform.core.plugin import DisableReason, PluginMetadata, PluginStatus
from quant_platform.core.registry import BaseRegistry
from tests.platform.fixtures.crash_plugin import PLUGIN_METADATA as CRASH_META
from tests.platform.fixtures.crash_plugin import factory as crash_factory
from tests.platform.fixtures.crash_plugin_dependent import PLUGIN_METADATA as DEP_META
from tests.platform.fixtures.crash_plugin_dependent import factory as dep_factory

TEST_GROUP = "platform.test.phase2b"


@pytest.fixture(autouse=True)
def _clean():
    reg = BaseRegistry.get_instance(TEST_GROUP)
    for meta in reg.list_plugins():
        reg.unregister(meta.name)
    yield


class TestDependencyResolver:
    def test_topological_sort(self):
        resolver = DependencyResolver()
        resolver.add_node("a", [])
        resolver.add_node("b", ["a"])
        assert resolver.topological_sort() == ["a", "b"]

    def test_cycle_detection(self):
        resolver = DependencyResolver()
        resolver.add_node("a", ["b"])
        resolver.add_node("b", ["a"])
        from quant_platform.core.registry import RegistryError

        with pytest.raises(RegistryError):
            resolver.topological_sort()

    def test_cascade_dependency_unmet(self):
        resolver = DependencyResolver()
        resolver.add_node("crash_plugin", [], status=PluginStatus.DISABLED, disable_reason=DisableReason.LOAD_CRASH)
        resolver.add_node("dependent", ["crash_plugin"])
        changed = resolver.cascade_disabled()
        assert "dependent" in changed


class TestCompatibility:
    def test_incompatible_version(self):
        reg = BaseRegistry.get_instance(TEST_GROUP)
        meta = PluginMetadata(
            name="old",
            version="1.0.0",
            platform_version_compatibility=">=99.0.0",
        )
        reg.register(meta, lambda: 1)
        checker = CompatibilityChecker()
        disabled = checker.enforce_registry(reg)
        assert "old" in disabled


class TestExecutionGraph:
    def test_execute_without_registry_lookup(self):
        calls: list[str] = []

        def step_a(ctx: PipelineContext) -> None:
            calls.append("a")
            ctx.emit(DataEnvelope(type_key="x", payload=1))

        def step_b(ctx: PipelineContext) -> None:
            calls.append("b")
            assert ctx.require("x").payload == 1

        graph = CompiledExecutionGraph(
            (ExecutionStep("a", step_a), ExecutionStep("b", step_b))
        )
        ctx = PipelineContext()
        graph.execute(ctx)
        assert calls == ["a", "b"]


class TestInstanceManager:
    def test_singleton_shared(self):
        mgr = InstanceManager()
        from quant_platform.core.plugin import PluginLifecycle

        calls = []

        def factory():
            calls.append(1)
            return object()

        a = mgr.get_or_create("k", PluginLifecycle.SINGLETON, factory)
        b = mgr.get_or_create("k", PluginLifecycle.SINGLETON, factory)
        assert a is b
        assert len(calls) == 1

    def test_scoped_cleared(self):
        mgr = InstanceManager()
        from quant_platform.core.plugin import PluginLifecycle

        a = mgr.get_or_create("k", PluginLifecycle.SCOPED, lambda: object(), run_id="run1")
        mgr.clear_scoped("run1")
        b = mgr.get_or_create("k", PluginLifecycle.SCOPED, lambda: object(), run_id="run1")
        assert a is not b


class TestSafeModeBatch:
    def test_crash_cascade(self):
        manager = PluginManager(plugins_config=PluginsConfig(safe_mode=True))
        reg = manager.registry(TEST_GROUP)
        reg.register(CRASH_META, crash_factory)
        reg.register(DEP_META, dep_factory)
        with pytest.raises(Exception):
            manager.get(TEST_GROUP, "crash_plugin")
        resolver = DependencyResolver.from_registry(reg)
        resolver.cascade_disabled()
