"""Composable reward functions."""

from __future__ import annotations

from quant_platform.core.context import PipelineContext
from quant_platform.interfaces.domain import RewardProtocol


class CompositeReward:
    def __init__(self, rewards: list[tuple[RewardProtocol, float]]) -> None:
        self._rewards = rewards

    def calculate(self, ctx: PipelineContext) -> float:
        total = 0.0
        for reward, weight in self._rewards:
            total += reward.calculate(ctx) * weight
        return total
