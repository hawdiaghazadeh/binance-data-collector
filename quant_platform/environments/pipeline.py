"""Environment plugin registration (Phase 11)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import PipelineContext
from quant_platform.core.manager import PluginManager
from quant_platform.registries.domain import ENVIRONMENT_GROUP


class EnvironmentRegistry:
    """Factory accessor for environment plugins."""

    def __init__(self, manager: PluginManager) -> None:
        self._manager = manager

    def create(self, name: str, **kwargs: Any) -> Any:
        return self._manager.get(ENVIRONMENT_GROUP, name, config=kwargs)


def register_environment_plugins(manager: PluginManager) -> None:
    from quant_platform.plugins.domain.futures_env import PLUGIN_METADATA as FUTURES_META
    from quant_platform.plugins.domain.futures_env import factory as futures_factory
    from quant_platform.plugins.domain.spot_env import PLUGIN_METADATA as SPOT_META
    from quant_platform.plugins.domain.spot_env import factory as spot_factory

    reg = manager.registry(ENVIRONMENT_GROUP)
    for meta, factory in [
        (SPOT_META, spot_factory),
        (FUTURES_META, futures_factory),
    ]:
        if meta.name not in {m.name for m in reg.list_plugins()}:
            reg.register(meta, factory)


def bootstrap_environment(
    manager: PluginManager,
    name: str,
    ctx: PipelineContext | None = None,
    *,
    prices: list[float] | None = None,
    **config: Any,
) -> Any:
    register_environment_plugins(manager)
    if prices is not None:
        config["prices"] = prices
    if ctx is not None:
        config["context"] = ctx
    return manager.get(ENVIRONMENT_GROUP, name, config=config)
