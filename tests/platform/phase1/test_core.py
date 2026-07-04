"""Phase 1 platform tests."""

from __future__ import annotations

import pytest

from quant_platform.core.config import ConfigValidationError, validate_plugin_config
from quant_platform.core.discovery import clear_pending, register
from quant_platform.core.manager import PluginManager, PluginsConfig
from quant_platform.core.plugin import (
    DisableReason,
    PluginLifecycle,
    PluginMetadata,
    PluginStatus,
)
from quant_platform.core.registry import BaseRegistry, PluginUnavailableError, RegistryError
from tests.platform.fixtures.crash_plugin import PLUGIN_METADATA as CRASH_META
from tests.platform.fixtures.crash_plugin import factory as crash_factory


TEST_GROUP = "platform.test.phase1"


@pytest.fixture(autouse=True)
def _clean_registry():
    clear_pending()
    reg = BaseRegistry.get_instance(TEST_GROUP)
    for meta in reg.list_plugins():
        reg.unregister(meta.name)
    yield
    clear_pending()


def _sample_meta(name: str = "test_plugin") -> PluginMetadata:
    return PluginMetadata(
        name=name,
        version="1.0.0",
        platform_version_compatibility=">=1.0.0,<2.0.0",
        lifecycle=PluginLifecycle.TRANSIENT,
    )


class TestPluginMetadata:
    def test_valid_semver(self):
        meta = _sample_meta()
        assert meta.version == "1.0.0"

    def test_invalid_semver_rejected(self):
        with pytest.raises(ValueError):
            PluginMetadata(
                name="bad",
                version="not-semver",
                platform_version_compatibility=">=1.0.0",
            )

    def test_invalid_platform_compat_rejected(self):
        with pytest.raises(ValueError):
            PluginMetadata(
                name="bad",
                version="1.0.0",
                platform_version_compatibility="not-a-spec",
            )


class TestBaseRegistry:
    def test_register_and_get(self):
        reg = BaseRegistry.get_instance(TEST_GROUP)
        meta = _sample_meta()
        reg.register(meta, lambda: "instance")
        assert reg.get("test_plugin") == "instance"

    def test_duplicate_registration_rejected(self):
        reg = BaseRegistry.get_instance(TEST_GROUP)
        meta = _sample_meta()
        reg.register(meta, lambda: 1)
        with pytest.raises(RegistryError):
            reg.register(meta, lambda: 2)

    def test_disabled_plugin_not_instantiated(self):
        reg = BaseRegistry.get_instance(TEST_GROUP)
        meta = _sample_meta()
        reg.register(meta, lambda: 1, status=PluginStatus.DISABLED, disable_reason=DisableReason.USER_CONFIG)
        with pytest.raises(PluginUnavailableError) as exc:
            reg.get("test_plugin")
        assert exc.value.disable_reason == DisableReason.USER_CONFIG


class TestSafeMode:
    def test_crash_plugin_disabled(self):
        manager = PluginManager(plugins_config=PluginsConfig(safe_mode=True))
        reg = manager.registry(TEST_GROUP)
        reg.register(CRASH_META, crash_factory)
        with pytest.raises(PluginUnavailableError) as exc:
            manager.get(TEST_GROUP, "crash_plugin")
        assert exc.value.disable_reason == DisableReason.LOAD_CRASH


class TestDecoratorRegister:
    def test_register_decorator(self):
        meta = _sample_meta("decorated")

        @register(TEST_GROUP, meta)
        def factory():
            return "decorated_instance"

        manager = PluginManager()
        manager.discover(TEST_GROUP)
        assert manager.get(TEST_GROUP, "decorated") == "decorated_instance"


class TestConfigValidation:
    def test_missing_required_field(self):
        schema = {"required": ["host"], "properties": {"host": {"type": "string"}}}
        with pytest.raises(ConfigValidationError):
            validate_plugin_config({}, schema)

    def test_valid_config(self):
        schema = {"required": ["host"], "properties": {"host": {"type": "string"}}}
        result = validate_plugin_config({"host": "localhost"}, schema)
        assert result["host"] == "localhost"
