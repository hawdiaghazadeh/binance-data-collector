"""RL product plugins (G30+)."""

from __future__ import annotations

from typing import Any, Callable

from quant_platform.core.manager import PluginManager
from quant_platform.core.plugin import PluginMetadata
from quant_platform.plugins.rl import episode_cache, training_dataset
from quant_platform.registries.rl_product import RL_GROUP, rl_registry

RL_PLUGIN_MODULES: list[Any] = [
    training_dataset,
    episode_cache,
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
