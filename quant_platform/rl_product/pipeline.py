"""RL product plugin registration (G30+)."""

from __future__ import annotations

from typing import Any, Callable

from quant_platform.core.manager import PluginManager
from quant_platform.core.plugin import PluginMetadata
from quant_platform.plugins.rl import RL_PLUGINS
from quant_platform.registries.domain import STRATEGY_GROUP
from quant_platform.registries.rl_product import RL_GROUP, rl_registry


def register_rl_product_plugins(manager: PluginManager) -> int:
    """Discover and register platform.rl plugins."""
    count = manager.discover(RL_GROUP, scan_packages=[])

    for meta, factory in RL_PLUGINS:
        if meta.name not in {m.name for m in rl_registry.list_plugins()}:
            rl_registry.register(meta, factory)
            count += 1

    count += _register_policy_strategy_hook(manager)
    return count


def _register_policy_strategy_hook(manager: PluginManager) -> int:
    from quant_platform.plugins.rl.policy_strategy import STRATEGY_PLUGIN_METADATA
    from quant_platform.plugins.rl.policy_strategy import factory as policy_strategy_factory

    strategy_reg = manager.registry(STRATEGY_GROUP)
    if STRATEGY_PLUGIN_METADATA.name in {m.name for m in strategy_reg.list_plugins()}:
        return 0
    strategy_reg.register(STRATEGY_PLUGIN_METADATA, policy_strategy_factory)
    return 1


RL_PLUGIN_ENTRIES: list[tuple[PluginMetadata, Callable[..., Any]]] = list(RL_PLUGINS)

__all__ = ["register_rl_product_plugins", "RL_PLUGIN_ENTRIES"]
