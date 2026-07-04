"""Optional curriculum scheduler plugin (G35)."""

from __future__ import annotations

from quant_platform.core.plugin import PluginMetadata
from quant_platform.rl_product.registry import RL_GROUP
from quant_platform.rl_product.training.curriculum import CurriculumScheduler

PLUGIN_METADATA = PluginMetadata(
    name="curriculum_scheduler",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Optional low-to-high volatility curriculum over training episodes",
    input_types=["episodes", "training_config"],
    output_types=["filtered_episodes"],
    registry_group=RL_GROUP,
)


class CurriculumSchedulerPlugin:
    def __init__(self, scheduler: CurriculumScheduler | None = None) -> None:
        self._scheduler = scheduler or CurriculumScheduler(enabled=False)

    @property
    def scheduler(self) -> CurriculumScheduler:
        return self._scheduler

    def filter_episodes(self, episodes: list, *, config: dict | None = None) -> list:
        if config is not None:
            self._scheduler = CurriculumScheduler.from_config(config)
        return self._scheduler.filter_episodes(episodes)


def factory(*, config: dict | None = None, **kwargs) -> CurriculumSchedulerPlugin:
    scheduler = CurriculumScheduler.from_config(config or {})
    return CurriculumSchedulerPlugin(scheduler)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
