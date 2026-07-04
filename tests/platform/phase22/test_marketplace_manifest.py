"""Phase 22 marketplace manifest tests."""

from __future__ import annotations

from pathlib import Path

from quant_platform.core.manager import PluginManager
from quant_platform.core.registry import BaseRegistry
from quant_platform.marketplace.cli import main
from quant_platform.marketplace.discovery import (
    discover_entry_points_from_manifest,
    register_plugins_from_manifest,
    verify_manifest_entry_points,
)
from quant_platform.marketplace.manifest import load_plugin_manifest, load_plugin_manifest_from_package
from quant_platform.marketplace.service import MarketplaceService
from quant_platform.marketplace.state import InstalledPluginStore
from tests.platform.phase22.test_marketplace_cli import FakePipRunner

TEST_GROUP = "platform.test.marketplace"
FIXTURE_PACKAGE = "tests.platform.fixtures.marketplace_plugin"
FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "marketplace_plugin"


@pytest.fixture
def clean_registry():
    reg = BaseRegistry.get_instance(TEST_GROUP)
    for meta in reg.list_plugins():
        reg.unregister(meta.name)
    yield reg
    for meta in reg.list_plugins():
        reg.unregister(meta.name)


class TestPluginManifest:
    def test_load_plugin_manifest(self):
        manifest = load_plugin_manifest(FIXTURE_ROOT / "plugin.yaml")
        assert manifest.name == "marketplace_feature"
        assert manifest.version == "1.0.0"
        assert manifest.registry_group == TEST_GROUP
        assert manifest.entry_points[TEST_GROUP]["marketplace_feature"].endswith(":factory")

    def test_load_plugin_manifest_from_package(self):
        manifest = load_plugin_manifest_from_package(FIXTURE_PACKAGE)
        assert manifest is not None
        assert manifest.package == FIXTURE_PACKAGE

    def test_register_plugins_from_manifest(self, clean_registry):
        manager = PluginManager()
        manifest = load_plugin_manifest_from_package(FIXTURE_PACKAGE)
        registered = register_plugins_from_manifest(manager, manifest)
        assert registered == [(TEST_GROUP, "marketplace_feature")]
        plugin = manager.get(TEST_GROUP, "marketplace_feature")
        assert plugin is not None

    def test_discover_entry_points_from_manifest(self):
        manifest = load_plugin_manifest_from_package(FIXTURE_PACKAGE)
        discovered = discover_entry_points_from_manifest(manifest)
        assert len(discovered) == 1
        group, meta, factory = discovered[0]
        assert group == TEST_GROUP
        assert meta.name == "marketplace_feature"
        assert callable(factory)

    def test_verify_manifest_entry_points_reports_missing_pip_metadata(self):
        manifest = load_plugin_manifest_from_package(FIXTURE_PACKAGE)
        mismatches = verify_manifest_entry_points(manifest)
        assert mismatches
        assert any("Missing pip entry point" in item for item in mismatches)


class TestMarketplaceManifestInstall:
    def test_install_uses_manifest_when_present(self, tmp_path, clean_registry):
        manager = PluginManager()
        service = MarketplaceService(
            manager,
            pip_runner=FakePipRunner(),
            state_store=InstalledPluginStore(tmp_path / "installed_plugins.yaml"),
        )
        result = service.install(FIXTURE_PACKAGE, group=TEST_GROUP)
        assert result.manifest is not None
        assert result.manifest.name == "marketplace_feature"
        assert result.installed[0].name == "marketplace_feature"

    def test_inspect_cli_shows_manifest(self, capsys):
        exit_code = main(["inspect", FIXTURE_PACKAGE])
        captured = capsys.readouterr()
        assert exit_code == 0
        assert "marketplace_feature" in captured.out
        assert "entry_point:" in captured.out
