"""RL product plugin registration (G30+)."""

from __future__ import annotations

from typing import Any, Callable

from quant_platform.core.manager import PluginManager
from quant_platform.core.plugin import PluginMetadata
from quant_platform.plugins.rl import RL_PLUGINS
from quant_platform.registries.rl_product import RL_GROUP, rl_registry


def register_rl_product_plugins(manager: PluginManager) -> int:
    """Discover and register platform.rl plugins."""
    count = manager.discover(RL_GROUP, scan_packages=[])

    for meta, factory in RL_PLUGINS:
        if meta.name not in {m.name for m in rl_registry.list_plugins()}:
            rl_registry.register(meta, factory)
            count += 1
    return count


RL_PLUGIN_ENTRIES: list[tuple[PluginMetadata, Callable[..., Any]]] = list(RL_PLUGINS)

__all__ = ["register_rl_product_plugins", "RL_PLUGIN_ENTRIES"]
