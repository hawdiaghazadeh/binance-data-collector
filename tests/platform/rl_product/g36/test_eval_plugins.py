"""G36 — plugin registration."""

from __future__ import annotations

import pytest

from quant_platform.core.manager import PluginManager
from quant_platform.core.registry import BaseRegistry
from quant_platform.plugins.rl import RL_PLUGINS
from quant_platform.rl_product.pipeline import register_rl_product_plugins
from quant_platform.rl_product.registry import RL_GROUP


@pytest.fixture(autouse=True)
def _clean_rl_registry():
    reg = BaseRegistry.get_instance(RL_GROUP)
    for meta in reg.list_plugins():
        reg.unregister(meta.name)
    yield


def test_g36_plugins_registered():
    manager = PluginManager()
    register_rl_product_plugins(manager)
    names = {meta.name for meta, _ in RL_PLUGINS}
    assert "walk_forward_rl_eval" in names
    assert "ablation_eval" in names
