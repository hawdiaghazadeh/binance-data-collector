"""Phase 22 marketplace CLI tests."""

from __future__ import annotations

import pytest
import yaml

from quant_platform.core.manager import PluginManager
from quant_platform.core.plugin import DisableReason, PluginMetadata, PluginStatus
from quant_platform.core.registry import BaseRegistry, RegistryError
from quant_platform.marketplace.cli import main
from quant_platform.marketplace.config_store import PluginConfigStore
from quant_platform.marketplace.pip_runner import MarketplaceError
from quant_platform.marketplace.service import MarketplaceService
from quant_platform.marketplace.state import InstalledPlugin, InstalledPluginStore
from tests.platform.fixtures.marketplace_plugin import PLUGIN_METADATA as MARKETPLACE_META
from tests.platform.fixtures.marketplace_plugin import factory as marketplace_factory

TEST_GROUP = "platform.test.marketplace"


class FakePipRunner:
    def __init__(self, *, on_upgrade=None) -> None:
        self.install_calls: list[str] = []
        self.upgrade_calls: list[str] = []
        self.uninstall_calls: list[str] = []
        self._on_upgrade = on_upgrade

    def install(self, package: str) -> None:
        self.install_calls.append(package)

    def upgrade(self, package: str) -> None:
        self.upgrade_calls.append(package)
        if self._on_upgrade is not None:
            self._on_upgrade()

    def uninstall(self, package: str) -> None:
        self.uninstall_calls.append(package)


@pytest.fixture
def clean_registry():
    reg = BaseRegistry.get_instance(TEST_GROUP)
    for meta in reg.list_plugins():
        reg.unregister(meta.name)
    yield reg
    for meta in reg.list_plugins():
        reg.unregister(meta.name)


@pytest.fixture
def marketplace_env(tmp_path, clean_registry):
    manager = PluginManager()
    clean_registry.register(MARKETPLACE_META, marketplace_factory)

    state_path = tmp_path / "installed_plugins.yaml"
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump({"plugins": {"disabled": ["marketplace_feature"]}}), encoding="utf-8")

    service = MarketplaceService(
        manager,
        pip_runner=FakePipRunner(),
        state_store=InstalledPluginStore(state_path),
        config_store=PluginConfigStore(config_path),
    )
    return service, state_path, config_path


class TestMarketplaceService:
    def test_install_discovers_new_plugin(self, tmp_path, clean_registry):
        manager = PluginManager()
        state_path = tmp_path / "installed_plugins.yaml"
        service = MarketplaceService(
            manager,
            pip_runner=FakePipRunner(),
            state_store=InstalledPluginStore(state_path),
        )

        result = service.install("tests.platform.fixtures.marketplace_plugin", group=TEST_GROUP)
        assert result.package == "tests.platform.fixtures.marketplace_plugin"
        assert len(result.installed) == 1
        assert result.installed[0].name == "marketplace_feature"
        assert state_path.exists()

    def test_enable_disable_and_persist_config(self, marketplace_env):
        service, _, config_path = marketplace_env
        service.disable(TEST_GROUP, "marketplace_feature", persist=True)
        reg = service._manager.registry(TEST_GROUP)
        assert reg.get_record("marketplace_feature").status == PluginStatus.DISABLED

        service.enable(TEST_GROUP, "marketplace_feature", persist=True)
        assert reg.get_record("marketplace_feature").status == PluginStatus.ENABLED
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert "marketplace_feature" not in payload["plugins"]["disabled"]

    def test_update_tracks_new_version(self, marketplace_env, clean_registry):
        service, _, _ = marketplace_env
        service._state.add(
            InstalledPlugin(
                group=TEST_GROUP,
                name="marketplace_feature",
                package="tests.platform.fixtures.marketplace_plugin",
                version="1.0.0",
                installed_at=InstalledPluginStore.now_iso(),
            )
        )

        def upgrade_plugin() -> None:
            clean_registry.unregister("marketplace_feature")
            upgraded_meta = PluginMetadata(
                name="marketplace_feature",
                version="1.1.0",
                platform_version_compatibility=">=1.0.0,<2.0.0",
                registry_group=TEST_GROUP,
            )
            clean_registry.register(upgraded_meta, marketplace_factory)

        service._pip = FakePipRunner(on_upgrade=upgrade_plugin)
        result = service.update(TEST_GROUP, "marketplace_feature")
        assert result.changed is True
        assert result.old_version == "1.0.0"
        assert result.new_version == "1.1.0"

    def test_remove_unregisters_and_uninstalls(self, marketplace_env):
        service, _, _ = marketplace_env
        service._state.add(
            InstalledPlugin(
                group=TEST_GROUP,
                name="marketplace_feature",
                package="tests.platform.fixtures.marketplace_plugin",
                version="1.0.0",
                installed_at=InstalledPluginStore.now_iso(),
            )
        )
        service.remove(TEST_GROUP, "marketplace_feature")
        reg = service._manager.registry(TEST_GROUP)
        with pytest.raises(RegistryError):
            reg.get_record("marketplace_feature")
        assert service._pip.uninstall_calls == ["tests.platform.fixtures.marketplace_plugin"]

    def test_install_without_discovery_raises(self, tmp_path, clean_registry):
        manager = PluginManager()
        service = MarketplaceService(
            manager,
            pip_runner=FakePipRunner(),
            state_store=InstalledPluginStore(tmp_path / "installed_plugins.yaml"),
        )
        with pytest.raises(MarketplaceError, match="No new plugins discovered"):
            service.install("empty-package", group=TEST_GROUP)


class TestMarketplaceCLI:
    def test_cli_list_and_enable(self, marketplace_env, capsys, monkeypatch):
        service, state_path, config_path = marketplace_env
        monkeypatch.setattr(
            "quant_platform.marketplace.cli.build_service",
            lambda **kwargs: service,
        )

        exit_code = main(
            [
                "--config",
                str(config_path),
                "--state",
                str(state_path),
                "list",
                "--group",
                TEST_GROUP,
            ]
        )
        captured = capsys.readouterr()
        assert exit_code == 0
        assert "marketplace_feature" in captured.out

        exit_code = main(
            [
                "--config",
                str(config_path),
                "--state",
                str(state_path),
                "enable",
                TEST_GROUP,
                "marketplace_feature",
            ]
        )
        captured = capsys.readouterr()
        assert exit_code == 0
        assert "enabled" in captured.out
        record = service._manager.registry(TEST_GROUP).get_record("marketplace_feature")
        assert record.status == PluginStatus.ENABLED
        assert record.disable_reason is None

    def test_cli_disable(self, marketplace_env, capsys, monkeypatch):
        service, state_path, config_path = marketplace_env
        monkeypatch.setattr(
            "quant_platform.marketplace.cli.build_service",
            lambda **kwargs: service,
        )

        exit_code = main(
            [
                "--config",
                str(config_path),
                "--state",
                str(state_path),
                "disable",
                TEST_GROUP,
                "marketplace_feature",
            ]
        )
        assert exit_code == 0
        record = service._manager.registry(TEST_GROUP).get_record("marketplace_feature")
        assert record.status == PluginStatus.DISABLED
        assert record.disable_reason == DisableReason.USER_CONFIG
