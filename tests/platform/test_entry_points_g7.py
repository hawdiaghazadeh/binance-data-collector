"""Entry point coverage tests (G7)."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
import tomllib

from quant_platform.core.discovery import discover_entry_points
from quant_platform.core.manager import PluginManager
from quant_platform.core.registry import BaseRegistry
from quant_platform.plugins.domain_reference import DOMAIN_PLUGINS, register_all_domain_plugins
from quant_platform.registries.groups import ALL_REGISTRY_GROUPS

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = PROJECT_ROOT / "pyproject.toml"


@pytest.fixture(autouse=True)
def _clean_domain_registries():
    for group, _, _ in DOMAIN_PLUGINS:
        reg = BaseRegistry.get_instance(group)
        for meta in reg.list_plugins():
            reg.unregister(meta.name)
    yield


def _load_pyproject_entry_points() -> dict[str, dict[str, str]]:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    return data["project"]["entry-points"]


class TestEntryPointManifest:
    def test_all_registry_groups_declared(self):
        entry_points = _load_pyproject_entry_points()
        missing = [group for group in ALL_REGISTRY_GROUPS if group not in entry_points]
        assert missing == []

    def test_each_group_has_at_least_one_plugin(self):
        entry_points = _load_pyproject_entry_points()
        for group in ALL_REGISTRY_GROUPS:
            assert entry_points[group]

    def test_entry_point_targets_are_importable(self):
        entry_points = _load_pyproject_entry_points()
        for group, plugins in entry_points.items():
            for name, target in plugins.items():
                module_path, attr = target.split(":", 1)
                module = importlib.import_module(module_path)
                factory = getattr(module, attr)
                assert callable(factory), f"{group}.{name} target is not callable"


class TestEntryPointDiscovery:
    def test_domain_plugins_discoverable_via_entry_points(self):
        manager = PluginManager()
        count = register_all_domain_plugins(manager)
        assert count >= 25
        assert manager.get("platform.normalizations", "symbol_normalizer") is not None

    def test_feature_entry_points_resolve_metadata(self):
        plugins = discover_entry_points("platform.features")
        if not plugins:
            pytest.skip("Feature entry points require editable install (pip install -e .)")
        names = {meta.name for meta, _ in plugins}
        assert {"ohlc_feature", "volume_feature", "atr_feature", "vwap_feature"}.issubset(names)
