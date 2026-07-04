"""Episode cache plugin — LRU + async prefetch (G30)."""

from __future__ import annotations

from collections.abc import Callable

from quant_platform.core.plugin import PluginMetadata
from quant_platform.rl_product.dataset.cache import EpisodeCache
from quant_platform.rl_product.protocols import Episode
from quant_platform.rl_product.registry import RL_GROUP

PLUGIN_METADATA = PluginMetadata(
    name="episode_cache",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="LRU episode cache with optional async prefetch",
    input_types=["episodes"],
    output_types=["episode"],
    registry_group=RL_GROUP,
)


class EpisodeCachePlugin:
    def __init__(self, *, maxsize: int = 4, prefetch: int = 2) -> None:
        self._cache = EpisodeCache(maxsize=maxsize, prefetch=prefetch)

    @property
    def cache(self) -> EpisodeCache:
        return self._cache

    def get(self, episode_id: str, loader: Callable[[], Episode]) -> Episode:
        return self._cache.get(episode_id, loader)

    def prefetch(self, episode_ids: list[str], loader: Callable[[str], Episode]) -> None:
        self._cache.prefetch(episode_ids, loader)

    def clear(self) -> None:
        self._cache.clear()

    def close(self) -> None:
        self._cache.close()


def factory(
    *,
    maxsize: int = 4,
    prefetch: int = 2,
    config: dict | None = None,
    **kwargs,
) -> EpisodeCachePlugin:
    if config:
        cache_cfg = config.get("cache", config.get("dataset", {}).get("cache", {}))
        maxsize = int(cache_cfg.get("maxsize", maxsize))
        prefetch = int(cache_cfg.get("prefetch", prefetch))
    return EpisodeCachePlugin(maxsize=maxsize, prefetch=prefetch)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
