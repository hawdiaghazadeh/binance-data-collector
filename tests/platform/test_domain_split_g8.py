"""Tests for split domain plugin packages (G8)."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from quant_platform.core.manager import PluginManager
from quant_platform.core.registry import BaseRegistry
from quant_platform.plugins.domain import DOMAIN_PLUGIN_MODULES, register_all_domain_plugins

DOMAIN_ROOT = Path(__file__).resolve().parents[2] / "quant_platform" / "plugins" / "domain"


@pytest.fixture(autouse=True)
def _clean_domain_registries():
    for group, _ in DOMAIN_PLUGIN_MODULES:
        reg = BaseRegistry.get_instance(group)
        for meta in reg.list_plugins():
            reg.unregister(meta.name)
    yield


class TestSplitDomainPackages:
    def test_each_domain_plugin_has_package(self):
        for _, module in DOMAIN_PLUGIN_MODULES:
            assert module.__file__ is not None
            assert "/domain/" in module.__file__.replace("\\", "/")

    def test_register_all_from_split_packages(self):
        manager = PluginManager()
        count = register_all_domain_plugins(manager)
        assert count >= 25
        assert manager.get("platform.strategies", "rule_based") is not None

    def test_entry_point_targets_use_domain_packages(self):
        import tomllib

        pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
        entry_points = tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["entry-points"]
        for group, module in DOMAIN_PLUGIN_MODULES:
            plugin_name = module.factory.PLUGIN_METADATA.name
            target = entry_points[group][plugin_name]
            assert target.startswith("quant_platform.plugins.domain.")
            assert target.endswith(":factory")

    def test_backward_compat_shim(self):
        from quant_platform.plugins import domain_reference

        assert domain_reference.register_all_domain_plugins is register_all_domain_plugins

    def test_individual_plugin_importable(self):
        module = importlib.import_module("quant_platform.plugins.domain.equity_curve")
        viz = module.factory()
        assert module.factory.PLUGIN_METADATA.registry_group == "platform.visualizations"
        ctx = __import__("quant_platform.core.context", fromlist=["PipelineContext"]).PipelineContext()
        assert viz.render(ctx)["type"] == "equity_curve"
