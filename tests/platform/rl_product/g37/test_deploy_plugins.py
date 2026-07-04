"""G37 — deploy plugin registration."""

from __future__ import annotations

import pytest

from quant_platform.core.manager import PluginManager
from quant_platform.core.registry import BaseRegistry
from quant_platform.plugins.rl import RL_PLUGINS
from quant_platform.registries.domain import STRATEGY_GROUP
from quant_platform.rl_product.pipeline import register_rl_product_plugins
from quant_platform.rl_product.registry import RL_GROUP


@pytest.fixture(autouse=True)
def _clean_registries():
    for group in (RL_GROUP, STRATEGY_GROUP):
        reg = BaseRegistry.get_instance(group)
        for meta in reg.list_plugins():
            reg.unregister(meta.name)
    yield


def test_g37_plugins_registered():
    manager = PluginManager()
    register_rl_product_plugins(manager)
    names = {meta.name for meta, _ in RL_PLUGINS}
    assert len(names) == 27
    assert "policy_inference" in names
    assert "model_registry" in names
    assert "policy_strategy" in names
    strategy = manager.get(STRATEGY_GROUP, "policy_strategy")
    assert hasattr(strategy, "on_bar")
    assert hasattr(strategy, "signals")
