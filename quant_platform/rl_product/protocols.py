"""RL product protocols and shared data types (G30+)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, Sequence, runtime_checkable

from services.shared.models import KlineRow

EpisodeSplit = Literal["train", "val", "test"]


@dataclass(frozen=True, slots=True)
class Episode:
    """Immutable episode window loaded once at reset()."""

    episode_id: str
    symbol: str
    timeframe: str
    bars: tuple[KlineRow, ...]
    split: EpisodeSplit
    start_idx: int


class EpisodeCursor:
    """In-memory cursor; exposes only bars[0:t+1] (no lookahead)."""

    __slots__ = ("_bars", "_t")

    def __init__(self, bars: Sequence[KlineRow], *, start: int = 0) -> None:
        if start < 0 or start >= len(bars):
            raise ValueError("start index out of range")
        self._bars = tuple(bars)
        self._t = start

    @property
    def t(self) -> int:
        return self._t

    @property
    def length(self) -> int:
        return len(self._bars)

    def view(self) -> list[KlineRow]:
        """Return bars[0:t+1] inclusive."""
        return list(self._bars[: self._t + 1])

    def current_bar(self) -> KlineRow:
        return self._bars[self._t]

    def advance(self) -> bool:
        if self._t >= len(self._bars) - 1:
            return False
        self._t += 1
        return True

    def reset(self, *, start: int = 0) -> None:
        if start < 0 or start >= len(self._bars):
            raise ValueError("start index out of range")
        self._t = start

    def is_done(self) -> bool:
        return self._t >= len(self._bars) - 1


@runtime_checkable
class TrainingDatasetProtocol(Protocol):
    def load_episodes(self, config: dict) -> list[Episode]: ...


@runtime_checkable
class EpisodeCacheProtocol(Protocol):
    def get(self, episode_id: str, loader: object) -> Episode: ...

    def prefetch(self, episode_ids: list[str], loader: object) -> None: ...

    def clear(self) -> None: ...
