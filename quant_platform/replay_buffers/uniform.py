"""Uniform replay buffer (Phase 15)."""

from __future__ import annotations

import random
from collections import deque
from typing import Any

from quant_platform.replay_buffers.source import normalize_transition


class UniformReplayBufferEngine:
    def __init__(self, *, capacity: int = 10_000) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be > 0")
        self._capacity = capacity
        self._buffer: deque[dict[str, Any]] = deque(maxlen=capacity)

    def add(self, transition: Any) -> None:
        self._buffer.append(normalize_transition(transition))

    def sample(self, batch_size: int) -> list[dict[str, Any]]:
        if batch_size <= 0:
            return []
        if not self._buffer:
            return []
        size = min(batch_size, len(self._buffer))
        return random.sample(list(self._buffer), size)

    def __len__(self) -> int:
        return len(self._buffer)

    def clear(self) -> None:
        self._buffer.clear()
