"""Reference domain plugin: uniform_buffer."""

from __future__ import annotations

from typing import Any

from quant_platform.plugins.domain._helpers import attach_factory_metadata, reference_meta

PLUGIN_METADATA = reference_meta("uniform_buffer", "platform.replay_buffers")


class UniformReplayBuffer:

    def __init__(self) -> None:
        self._buffer: list = []

    def add(self, transition: Any) -> None:
        self._buffer.append(transition)

    def sample(self, batch_size: int) -> list:
        return self._buffer[:batch_size]


def factory(**kwargs) -> UniformReplayBuffer:
    return UniformReplayBuffer()


attach_factory_metadata(factory, PLUGIN_METADATA)
