"""Phase 5 discovery expansion tests (G5)."""

from __future__ import annotations

import pytest

from quant_platform.core.discovery import (
    clear_pending,
    discover_dynamic_import,
    discover_package_plugins,
    discover_reflection_plugins,
    iter_discovery_sources,
)
from quant_platform.core.manager import PluginManager, PluginsConfig
from quant_platform.core.plugin import PluginLifecycle, PluginMetadata
from quant_platform.core.registry import BaseRegistry
from quant_platform.registries.feature import FEATURE_GROUP
from tests.platform.fixtures.reflection_feature import ReflectionFeaturePlugin

TEST_GROUP = "platform.test.g5"
DYNAMIC_MODULE = "tests.platform.fixtures.dynamic_feature"
REFLECTION_MODULE = "tests.platform.fixtures.reflection_feature"


@pytest.fixture(autouse=True)
def _clean():
    clear_pending()
    reg = BaseRegistry.get_instance(TEST_GROUP)
    for meta in reg.list_plugins():
        reg.unregister(meta.name)
    yield
    clear_pending()


class TestDynamicImportDiscovery:
    def test_discover_dynamic_import(self):
        plugins = discover_dynamic_import(DYNAMIC_MODULE, TEST_GROUP)
        assert len(plugins) == 1
        meta, factory = plugins[0]
        assert meta.name == "dynamic_feature"
        assert factory() is not None

    def test_wrong_group_skipped(self):
        assert discover_dynamic_import(DYNAMIC_MODULE, "platform.other") == []


class TestReflectionDiscovery:
    def test_discover_reflection_plugins(self):
        plugins = discover_reflection_plugins(REFLECTION_MODULE, TEST_GROUP)
        assert len(plugins) == 1
        meta, factory = plugins[0]
        assert meta.name == "reflection_feature"
        assert isinstance(factory(), ReflectionFeaturePlugin)


class TestPackageScanDiscovery:
    def test_discover_feature_plugins_from_package(self):
        plugins = discover_package_plugins("quant_platform.plugins", FEATURE_GROUP)
        names = {meta.name for meta, _ in plugins}
        assert "ohlc_feature" in names
        assert "atr_feature" in names


class TestPluginManagerDiscovery:
    def test_manager_uses_dynamic_and_reflection_config(self):
        manager = PluginManager(
            plugins_config=PluginsConfig(
                dynamic_modules=[DYNAMIC_MODULE],
                reflection_modules=[REFLECTION_MODULE],
                scan_packages=[],
            )
        )
        count = manager.discover(TEST_GROUP)
        assert count == 2
        assert manager.get(TEST_GROUP, "dynamic_feature") is not None
        assert manager.get(TEST_GROUP, "reflection_feature") is not None

    def test_duplicate_discovery_skipped(self):
        manager = PluginManager(
            plugins_config=PluginsConfig(
                dynamic_modules=[DYNAMIC_MODULE, DYNAMIC_MODULE],
                scan_packages=[],
            )
        )
        assert manager.discover(TEST_GROUP) == 1


class TestIterDiscoverySources:
    def test_iterates_all_mechanisms(self):
        meta = PluginMetadata(
            name="decorated_g5",
            version="1.0.0",
            platform_version_compatibility=">=1.0.0,<2.0.0",
            lifecycle=PluginLifecycle.TRANSIENT,
            registry_group=TEST_GROUP,
        )

        from quant_platform.core.discovery import register

        @register(TEST_GROUP, meta)
        def decorated_factory():
            return "decorated"

        sources = list(
            iter_discovery_sources(
                TEST_GROUP,
                scan_packages=[],
                dynamic_modules=[DYNAMIC_MODULE],
                reflection_modules=[REFLECTION_MODULE],
            )
        )
        names = {meta.name for meta, _ in sources}
        assert "decorated_g5" in names
        assert "dynamic_feature" in names
        assert "reflection_feature" in names
