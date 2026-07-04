"""Rollout batch container (G34)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class RolloutBatch:
    observations: Any
    actions: Any
    log_probs: Any
    rewards: Any
    values: Any
    dones: Any
    advantages: Any | None = None
    returns: Any | None = None

    @property
    def batch_size(self) -> int:
        return int(self.observations.shape[0])
