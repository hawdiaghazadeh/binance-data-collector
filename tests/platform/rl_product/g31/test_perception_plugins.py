"""G31 — perception plugin registration."""

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


def test_g31_plugins_registered():
    manager = PluginManager()
    count = register_rl_product_plugins(manager)
    assert count >= 15
    names = {meta.name for meta, _ in RL_PLUGINS}
    assert len(names) == 15
    expected = {
        "training_dataset",
        "episode_cache",
        "smc_bos_prob",
        "smc_choch_prob",
        "smc_ob_validity_prob",
        "smc_fvg_fill_prob",
        "rtm_sd_strength",
        "rtm_sweep_prob",
        "rtm_compression_prob",
        "rtm_flip_prob",
        "ict_session_prob",
        "ict_killzone_prob",
        "ict_premium_discount_prob",
        "perception_compressor",
        "feature_gate",
    }
    assert names == expected
