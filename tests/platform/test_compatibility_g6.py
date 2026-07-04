"""Cross-version compatibility matrix tests (G6)."""

from __future__ import annotations

import pytest

from quant_platform.bootstrap import bootstrap_pipeline
from quant_platform.core.compatibility import (
    CompatibilityChecker,
    CompatibilityContext,
    build_compatibility_context,
    version_matches_spec,
)
from quant_platform.core.manager import PluginManager
from quant_platform.core.plugin import DisableReason, PluginMetadata, PluginStatus
from quant_platform.core.registry import BaseRegistry
from quant_platform.features.pipeline import register_feature_plugins
from quant_platform.registries.feature import FEATURE_GROUP
from services.shared.config import AppConfig, PathsConfig

TEST_GROUP = "platform.test.g6"


@pytest.fixture(autouse=True)
def _clean():
    reg = BaseRegistry.get_instance(TEST_GROUP)
    for meta in reg.list_plugins():
        reg.unregister(meta.name)
    yield


class TestVersionMatcher:
    def test_version_matches_spec(self):
        assert version_matches_spec("1.0.0", ">=1.0.0,<2.0.0")
        assert not version_matches_spec("2.0.0", ">=1.0.0,<2.0.0")


class TestCrossVersionMatrix:
    def test_dataset_version_rejection(self):
        meta = PluginMetadata(
            name="needs_new_dataset",
            version="1.0.0",
            platform_version_compatibility=">=1.0.0,<2.0.0",
            compatible_dataset_versions=">=2.0.0",
        )
        checker = CompatibilityChecker(context=CompatibilityContext(dataset_version="1.0.0"))
        assert not checker.is_compatible(meta)
        assert "Dataset 1.0.0" in checker.incompatibility_reason(meta)

    def test_feature_version_rejection(self):
        meta = PluginMetadata(
            name="needs_new_features",
            version="1.0.0",
            platform_version_compatibility=">=1.0.0,<2.0.0",
            compatible_feature_versions=">=2.0.0",
        )
        checker = CompatibilityChecker(
            context=CompatibilityContext(feature_versions={"ohlc_feature": "1.0.0"})
        )
        assert not checker.is_compatible(meta)

    def test_missing_context_skips_optional_checks(self):
        meta = PluginMetadata(
            name="optional_matrix",
            version="1.0.0",
            platform_version_compatibility=">=1.0.0,<2.0.0",
            compatible_dataset_versions=">=2.0.0",
            compatible_feature_versions=">=2.0.0",
        )
        checker = CompatibilityChecker(context=CompatibilityContext())
        assert checker.is_compatible(meta)

    def test_enforce_registry_disables_incompatible_plugin(self):
        reg = BaseRegistry.get_instance(TEST_GROUP)
        reg.register(
            PluginMetadata(
                name="bad_dataset_match",
                version="1.0.0",
                platform_version_compatibility=">=1.0.0,<2.0.0",
                compatible_dataset_versions=">=9.0.0",
            ),
            lambda: 1,
        )
        checker = CompatibilityChecker(context=CompatibilityContext(dataset_version="1.0.0"))
        disabled = checker.enforce_registry(reg)
        assert disabled == ["bad_dataset_match"]
        record = reg.get_record("bad_dataset_match")
        assert record.status == PluginStatus.DISABLED
        assert record.disable_reason == DisableReason.INCOMPATIBLE_VERSION


class TestBuildCompatibilityContext:
    def test_collects_dataset_and_feature_versions(self):
        runtime = bootstrap_pipeline(_test_config())
        register_feature_plugins(runtime.manager)
        context = build_compatibility_context(runtime.manager)
        assert context.dataset_version == "1.0.0"
        assert context.feature_versions["ohlc_feature"] == "1.0.0"


def _test_config() -> AppConfig:
    return AppConfig(
        symbols=["BTCUSDT"],
        timeframes=["1h"],
        paths=PathsConfig(download_dir="./downloads", logs_dir="./logs", state_dir="./downloads/.state"),
    )


class TestFeatureBootstrapCompatibility:
    def test_ohlc_feature_compatible_with_default_dataset(self):
        runtime = bootstrap_pipeline(_test_config())
        register_feature_plugins(runtime.manager)
        context = build_compatibility_context(runtime.manager)
        checker = CompatibilityChecker(context=context)
        ohlc = runtime.manager.registry(FEATURE_GROUP).get_record("ohlc_feature").metadata
        assert checker.is_dataset_compatible(ohlc)

    def test_incompatible_feature_disabled_on_enforce(self):
        manager = PluginManager()
        register_feature_plugins(manager)
        runtime = bootstrap_pipeline(_test_config())
        manager = runtime.manager
        register_feature_plugins(manager)
        reg = manager.registry(FEATURE_GROUP)
        reg.register(
            PluginMetadata(
                name="strict_feature",
                version="1.0.0",
                platform_version_compatibility=">=1.0.0,<2.0.0",
                compatible_feature_versions=">=99.0.0",
                registry_group=FEATURE_GROUP,
            ),
            lambda: object(),
        )
        context = build_compatibility_context(manager)
        checker = CompatibilityChecker(context=context)
        disabled = checker.enforce_registry(reg)
        assert "strict_feature" in disabled
