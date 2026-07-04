"""G33 — gymnasium wrapper and plugin registration."""

from __future__ import annotations

import pytest

from quant_platform.core.manager import PluginManager
from quant_platform.core.registry import BaseRegistry
from quant_platform.plugins.rl import RL_PLUGINS
from quant_platform.plugins.rl.rl_env_spot import RlEnvSpotPlugin
from quant_platform.rl_product.env.gym_wrapper import GymnasiumRLEnv
from quant_platform.rl_product.pipeline import register_rl_product_plugins
from quant_platform.rl_product.registry import RL_GROUP
from tests.platform.rl_product.g33.conftest import default_config, trending_episode

gymnasium = pytest.importorskip("gymnasium")


@pytest.fixture(autouse=True)
def _clean_rl_registry():
    reg = BaseRegistry.get_instance(RL_GROUP)
    for meta in reg.list_plugins():
        reg.unregister(meta.name)
    yield


def test_g33_plugins_registered():
    manager = PluginManager()
    count = register_rl_product_plugins(manager)
    assert count >= 19
    names = {meta.name for meta, _ in RL_PLUGINS}
    assert "execution_model" in names
    assert "rl_env_spot" in names
    assert "rl_env_futures" in names


def test_gymnasium_wrapper_spaces():
    plugin = RlEnvSpotPlugin()
    bridge = plugin.create(trending_episode(25), config=default_config())
    env = GymnasiumRLEnv(bridge)
    assert env.observation_space.shape == (128,)
    assert env.action_space.shape == (1,)
    obs, info = env.reset()
    assert len(obs) == 128
    obs, reward, terminated, truncated, info = env.step([0.4])
    assert len(obs) == 128
    assert isinstance(reward, float)
