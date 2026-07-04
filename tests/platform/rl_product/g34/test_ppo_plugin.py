"""G34 — ppo_torch plugin registration."""

from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")

from quant_platform.core.manager import PluginManager
from quant_platform.core.registry import BaseRegistry
from quant_platform.plugins.rl.ppo_torch import PpoTorchPlugin
from quant_platform.rl_product.pipeline import register_rl_product_plugins
from quant_platform.rl_product.registry import RL_GROUP
from tests.platform.rl_product.g34.conftest import default_agent_config


@pytest.fixture(autouse=True)
def _clean_rl_registry():
    reg = BaseRegistry.get_instance(RL_GROUP)
    for meta in reg.list_plugins():
        reg.unregister(meta.name)
    yield


def test_ppo_torch_plugin_registered():
    manager = PluginManager()
    register_rl_product_plugins(manager)
    assert manager.get(RL_GROUP, "ppo_torch") is not None


def test_ppo_torch_plugin_build_and_save(tmp_path):
    plugin = PpoTorchPlugin()
    config = default_agent_config()
    trainer = plugin.build_trainer(config)
    assert trainer.model is not None
    path = tmp_path / "model.pt"
    plugin.save(str(path), config=config)
    loaded = plugin.load(str(path), config=config)
    assert loaded.model is not None
