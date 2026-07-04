"""Phase 22 marketplace hot-reload tests."""

from __future__ import annotations

import pytest
import yaml

from quant_platform.bootstrap import bootstrap_pipeline
from quant_platform.core.manager import PluginManager
from quant_platform.core.plugin import DisableReason, PluginMetadata, PluginStatus
from quant_platform.core.registry import BaseRegistry, PluginUnavailableError
from quant_platform.marketplace.cli import main
from quant_platform.marketplace.reload import reload_from_config_path, reload_pipeline_runtime, sync_plugin_status_from_config
from quant_platform.registries.pipeline import DATA_PROVIDER_GROUP
from services.shared.config import AppConfig, PathsConfig, PluginsConfigSection


def _test_config(*, disabled: list[str] | None = None) -> AppConfig:
    return AppConfig(
        symbols=["BTCUSDT"],
        timeframes=["1h"],
        paths=PathsConfig(download_dir="./downloads", logs_dir="./logs", state_dir="./downloads/.state"),
        plugins=PluginsConfigSection(disabled=disabled or []),
    )


TEST_GROUP = "platform.test.reload"


@pytest.fixture
def clean_test_registry():
    reg = BaseRegistry.get_instance(TEST_GROUP)
    for meta in reg.list_plugins():
        reg.unregister(meta.name)
    yield reg
    for meta in reg.list_plugins():
        reg.unregister(meta.name)


class TestSyncPluginStatus:
    def test_sync_disables_plugin_from_config(self, clean_test_registry):
        meta = PluginMetadata(
            name="reload_plugin",
            version="1.0.0",
            platform_version_compatibility=">=1.0.0,<2.0.0",
            registry_group=TEST_GROUP,
        )
        clean_test_registry.register(meta, lambda: object())
        manager = PluginManager()
        config = _test_config(disabled=["reload_plugin"])
        _, disabled = sync_plugin_status_from_config(manager, config)
        assert disabled == 1
        record = manager.registry(TEST_GROUP).get_record("reload_plugin")
        assert record.status == PluginStatus.DISABLED
        assert record.disable_reason == DisableReason.USER_CONFIG


class TestHotReload:
    def test_reload_rebuilds_execution_graph_and_instances(self):
        runtime = bootstrap_pipeline(_test_config())
        original_graph = runtime.execution_graph
        original_provider = runtime.data_provider

        rebuilt, (enabled, disabled) = reload_pipeline_runtime(runtime, _test_config())
        assert rebuilt.execution_graph is not original_graph
        assert rebuilt.data_provider is not original_provider
        assert len(rebuilt.execution_graph) == 3

    def test_reload_applies_updated_disabled_list(self, tmp_path, clean_test_registry):
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            yaml.safe_dump(
                {
                    "symbols": ["BTCUSDT"],
                    "timeframes": ["1h"],
                    "paths": {
                        "download_dir": "./downloads",
                        "logs_dir": "./logs",
                        "state_dir": "./downloads/.state",
                    },
                    "plugins": {"disabled": []},
                }
            ),
            encoding="utf-8",
        )

        runtime = bootstrap_pipeline(_test_config())
        meta = PluginMetadata(
            name="reload_plugin",
            version="1.0.0",
            platform_version_compatibility=">=1.0.0,<2.0.0",
            registry_group=TEST_GROUP,
        )
        clean_test_registry.register(meta, lambda: object())
        runtime.manager.registry(TEST_GROUP)

        config_path.write_text(
            yaml.safe_dump(
                {
                    "symbols": ["BTCUSDT"],
                    "timeframes": ["1h"],
                    "paths": {
                        "download_dir": "./downloads",
                        "logs_dir": "./logs",
                        "state_dir": "./downloads/.state",
                    },
                    "plugins": {"disabled": ["reload_plugin"]},
                }
            ),
            encoding="utf-8",
        )

        rebuilt, result = reload_from_config_path(config_path, runtime=runtime)
        record = rebuilt.manager.registry(TEST_GROUP).get_record("reload_plugin")
        assert record.status == PluginStatus.DISABLED
        assert result.plugins_disabled >= 1
        with pytest.raises(PluginUnavailableError):
            rebuilt.manager.get(TEST_GROUP, "reload_plugin")
        rebuilt.shutdown()

    def test_cli_reload_command(self, tmp_path, capsys):
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            yaml.safe_dump(
                {
                    "symbols": ["BTCUSDT"],
                    "timeframes": ["1h"],
                    "paths": {
                        "download_dir": "./downloads",
                        "logs_dir": "./logs",
                        "state_dir": "./downloads/.state",
                    },
                }
            ),
            encoding="utf-8",
        )
        exit_code = main(["--config", str(config_path), "reload", "--runtime-bootstrap"])
        captured = capsys.readouterr()
        assert exit_code == 0
        assert "reloaded" in captured.out
        assert "graph_steps=3" in captured.out
