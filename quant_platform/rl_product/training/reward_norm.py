"""Running reward normalization with sigma clipping (G35)."""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class RewardNormalizer:
    clip_sigma: float = 5.0
    warmup_steps: int = 0
    mean: float = 0.0
    m2: float = 0.0
    count: int = 0
    _warmup_seen: int = field(default=0, repr=False)

    def reset(self) -> None:
        self.mean = 0.0
        self.m2 = 0.0
        self.count = 0
        self._warmup_seen = 0

    @property
    def std(self) -> float:
        if self.count < 2:
            return 1.0
        variance = self.m2 / self.count
        return math.sqrt(max(variance, 1e-8))

    def update(self, reward: float) -> None:
        if self._warmup_seen < self.warmup_steps:
            self._warmup_seen += 1
            return
        self.count += 1
        delta = reward - self.mean
        self.mean += delta / self.count
        delta2 = reward - self.mean
        self.m2 += delta * delta2

    def normalize(self, reward: float, *, update: bool = True) -> float:
        if update:
            self.update(reward)
        if self.count < 2 and self._warmup_seen <= self.warmup_steps:
            return reward
        std = self.std
        normalized = (reward - self.mean) / std
        if self.clip_sigma > 0:
            normalized = max(-self.clip_sigma, min(self.clip_sigma, normalized))
        return normalized

    def stats(self) -> dict[str, float]:
        return {"mean": self.mean, "std": self.std, "count": float(self.count)}

    @classmethod
    def from_config(cls, config: dict) -> RewardNormalizer:
        reward = config.get("reward", config)
        training = config.get("training", {})
        return cls(
            clip_sigma=float(reward.get("clip_sigma", 5.0)),
            warmup_steps=int(training.get("reward_warmup_steps", reward.get("warmup_steps", 0))),
        )
