"""Training dataset plugin — loads OHLCV range and builds episodes (G30)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.plugin import PluginMetadata
from quant_platform.rl_product.dataset.episode import EpisodeBuilder
from quant_platform.rl_product.dataset.loader import TrainingDatasetLoader
from quant_platform.rl_product.protocols import Episode
from quant_platform.rl_product.registry import RL_GROUP

PLUGIN_METADATA = PluginMetadata(
    name="training_dataset",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Load ClickHouse OHLCV range and build train/val/test episodes",
    input_types=["training_config", "storage_backend"],
    output_types=["episodes"],
    registry_group=RL_GROUP,
)


class TrainingDatasetPlugin:
    def __init__(self, storage_backend: Any | None = None) -> None:
        self._storage_backend = storage_backend
        self._loader: TrainingDatasetLoader | None = None
        self._last_episodes: list[Episode] = []

    @property
    def loader(self) -> TrainingDatasetLoader | None:
        return self._loader

    @property
    def last_episodes(self) -> list[Episode]:
        return list(self._last_episodes)

    def load_episodes(self, config: dict, *, storage_backend: Any | None = None) -> list[Episode]:
        backend = storage_backend or self._storage_backend
        if backend is None:
            raise ValueError("storage_backend is required")
        self._loader = TrainingDatasetLoader(backend)
        bars = self._loader.load_from_config(config)
        episodes = EpisodeBuilder.build_from_config(bars, config)
        self._last_episodes = episodes
        return episodes


def factory(*, storage_backend: Any = None, config: dict | None = None, **kwargs) -> TrainingDatasetPlugin:
    plugin = TrainingDatasetPlugin(storage_backend=storage_backend)
    if config:
        plugin.load_episodes(config, storage_backend=storage_backend)
    return plugin


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
