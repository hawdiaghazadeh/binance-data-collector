"""Uniform replay buffer plugin (Phase 15)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.plugin import PluginMetadata
from quant_platform.replay_buffers.uniform import UniformReplayBufferEngine

PLUGIN_METADATA = PluginMetadata(
    name="uniform_buffer",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Fixed-capacity uniform random replay buffer",
    input_types=["transition"],
    output_types=["replay_batch"],
    registry_group="platform.replay_buffers",
)


class UniformReplayBuffer:
    def __init__(self, engine: UniformReplayBufferEngine) -> None:
        self._engine = engine

    def add(self, transition: Any) -> None:
        self._engine.add(transition)

    def sample(self, batch_size: int) -> list[dict[str, Any]]:
        return self._engine.sample(batch_size)

    def __len__(self) -> int:
        return len(self._engine)


def factory(*, capacity: int = 10_000, config: dict | None = None, **kwargs) -> UniformReplayBuffer:
    if config and "capacity" in config:
        capacity = int(config["capacity"])
    return UniformReplayBuffer(UniformReplayBufferEngine(capacity=capacity))


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
