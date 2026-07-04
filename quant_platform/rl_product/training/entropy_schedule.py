"""Entropy coefficient linear schedule (G35)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EntropySchedule:
    start: float = 0.01
    end: float = 0.001
    min_coef: float = 0.0005
    total_steps: int = 2_000_000

    def coef_at(self, step: int) -> float:
        if self.total_steps <= 0:
            return max(self.min_coef, self.start)
        progress = min(max(step / self.total_steps, 0.0), 1.0)
        value = self.start + (self.end - self.start) * progress
        return max(self.min_coef, value)

    @classmethod
    def from_config(cls, config: dict) -> EntropySchedule:
        agent = config.get("agent", config)
        training = config.get("training", config)
        total = int(agent.get("total_timesteps", training.get("total_timesteps", 2_000_000)))
        return cls(
            start=float(agent.get("entropy_coef_start", 0.01)),
            end=float(agent.get("entropy_coef_end", 0.001)),
            min_coef=float(agent.get("entropy_coef_min", 0.0005)),
            total_steps=total,
        )
