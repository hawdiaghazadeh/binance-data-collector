"""Optional curriculum — low to high volatility episodes (G35)."""

from __future__ import annotations

import math
from dataclasses import dataclass

from quant_platform.rl_product.protocols import Episode


def _episode_volatility(episode: Episode, window: int = 20) -> float:
    closes = [bar.close for bar in episode.bars]
    if len(closes) < 2:
        return 0.0
    rets: list[float] = []
    for i in range(1, len(closes)):
        prev = closes[i - 1]
        if prev <= 0:
            rets.append(0.0)
        else:
            rets.append(math.log(closes[i] / prev))
    sample = rets[-window:]
    if not sample:
        return 0.0
    mean = sum(sample) / len(sample)
    var = sum((r - mean) ** 2 for r in sample) / len(sample)
    return math.sqrt(var)


@dataclass(frozen=True, slots=True)
class CurriculumStage:
    name: str
    vol_percentile_max: float
    timesteps: int


@dataclass
class CurriculumScheduler:
    enabled: bool = False
    stages: list[CurriculumStage] | None = None
    _stage_index: int = 0
    _stage_steps: int = 0

    @classmethod
    def from_config(cls, config: dict) -> CurriculumScheduler:
        training = config.get("training", config)
        curriculum = training.get("curriculum", {})
        if not curriculum or not curriculum.get("enabled", False):
            return cls(enabled=False)
        stages = [
            CurriculumStage(
                name=str(s.get("name", f"stage_{i}")),
                vol_percentile_max=float(s.get("vol_percentile_max", 100)),
                timesteps=int(s.get("timesteps", 0)),
            )
            for i, s in enumerate(curriculum.get("stages", []))
        ]
        return cls(enabled=True, stages=stages or None)

    def current_stage(self) -> CurriculumStage | None:
        if not self.enabled or not self.stages:
            return None
        idx = min(self._stage_index, len(self.stages) - 1)
        return self.stages[idx]

    def advance(self, steps: int) -> None:
        if not self.enabled or not self.stages:
            return
        self._stage_steps += steps
        stage = self.current_stage()
        if stage and stage.timesteps > 0 and self._stage_steps >= stage.timesteps:
            if self._stage_index < len(self.stages) - 1:
                self._stage_index += 1
                self._stage_steps = 0

    def filter_episodes(self, episodes: list[Episode]) -> list[Episode]:
        if not self.enabled or not episodes:
            return episodes
        stage = self.current_stage()
        if stage is None:
            return episodes
        vols = [_episode_volatility(ep) for ep in episodes]
        if not vols:
            return episodes
        sorted_vols = sorted(vols)
        cutoff_idx = int((stage.vol_percentile_max / 100.0) * (len(sorted_vols) - 1))
        cutoff_idx = max(0, min(cutoff_idx, len(sorted_vols) - 1))
        cutoff = sorted_vols[cutoff_idx]
        return [ep for ep, vol in zip(episodes, vols, strict=True) if vol <= cutoff + 1e-12]
