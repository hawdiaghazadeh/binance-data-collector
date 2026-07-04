"""G32 — price_action_observation plugin registration."""

from __future__ import annotations

import pytest

from quant_platform.core.manager import PluginManager
from quant_platform.core.registry import BaseRegistry
from quant_platform.plugins.rl.price_action_observation import PriceActionObservationPlugin
from quant_platform.rl_product.pipeline import register_rl_product_plugins
from quant_platform.rl_product.registry import RL_GROUP
from tests.platform.rl_product.g32.conftest import trending_bars


@pytest.fixture(autouse=True)
def _clean_rl_registry():
    reg = BaseRegistry.get_instance(RL_GROUP)
    for meta in reg.list_plugins():
        reg.unregister(meta.name)
    yield


def test_plugin_registered():
    manager = PluginManager()
    register_rl_product_plugins(manager)
    plugin = manager.get(RL_GROUP, "price_action_observation")
    assert plugin is not None


def test_plugin_builds_vector():
    plugin = PriceActionObservationPlugin()
    bars = trending_bars(50)
    config = {"observation": {"dim": 128, "context_dims": 16}, "perception": {"master_gate": 1.0}}
    obs = plugin.build(bars, 49, config=config)
    assert obs.metadata()["schema_version"] == "1.0"
    assert len(obs.to_list()) == 128
