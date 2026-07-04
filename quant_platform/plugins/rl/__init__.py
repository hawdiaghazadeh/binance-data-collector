"""RL product plugins (G30+)."""

from __future__ import annotations

from typing import Any, Callable

from quant_platform.core.manager import PluginManager
from quant_platform.core.plugin import PluginMetadata
from quant_platform.plugins.rl import (
    episode_cache,
    execution_model,
    feature_gate,
    ict_killzone_prob,
    ict_premium_discount_prob,
    ict_session_prob,
    perception_compressor,
    ppo_torch,
    online_training,
    curriculum_scheduler,
    walk_forward_rl_eval,
    ablation_eval,
    price_action_observation,
    rl_env_futures,
    rl_env_spot,
    rtm_compression_prob,
    rtm_flip_prob,
    rtm_sd_strength,
    rtm_sweep_prob,
    smc_bos_prob,
    smc_choch_prob,
    smc_fvg_fill_prob,
    smc_ob_validity_prob,
    training_dataset,
)
from quant_platform.registries.rl_product import RL_GROUP, rl_registry

RL_PLUGIN_MODULES: list[Any] = [
    training_dataset,
    episode_cache,
    smc_bos_prob,
    smc_choch_prob,
    smc_ob_validity_prob,
    smc_fvg_fill_prob,
    rtm_sd_strength,
    rtm_sweep_prob,
    rtm_compression_prob,
    rtm_flip_prob,
    ict_session_prob,
    ict_killzone_prob,
    ict_premium_discount_prob,
    perception_compressor,
    feature_gate,
    price_action_observation,
    execution_model,
    rl_env_spot,
    rl_env_futures,
    ppo_torch,
    online_training,
    curriculum_scheduler,
    walk_forward_rl_eval,
    ablation_eval,
]

RL_PLUGINS: list[tuple[PluginMetadata, Callable[..., Any]]] = [
    (module.factory.PLUGIN_METADATA, module.factory) for module in RL_PLUGIN_MODULES
]


def register_rl_plugins(manager: PluginManager) -> int:
    count = manager.discover(RL_GROUP, scan_packages=[])
    for meta, factory in RL_PLUGINS:
        if meta.name not in {m.name for m in rl_registry.list_plugins()}:
            rl_registry.register(meta, factory)
            count += 1
    return count
