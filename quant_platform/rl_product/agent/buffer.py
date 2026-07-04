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
        obs = self.observations
        if hasattr(obs, "shape"):
            return int(obs.shape[0])
        return len(obs)
