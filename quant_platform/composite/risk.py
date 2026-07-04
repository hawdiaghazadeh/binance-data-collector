"""Composable risk checks."""

from __future__ import annotations

from quant_platform.core.context import PipelineContext
from quant_platform.interfaces.domain import RiskProtocol


class CompositeRisk:
    def __init__(self, risks: list[RiskProtocol]) -> None:
        self._risks = risks

    def check(self, ctx: PipelineContext, order: object) -> bool:
        return all(r.check(ctx, order) for r in self._risks)

    def position_size(self, ctx: PipelineContext) -> float:
        if not self._risks:
            return 0.0
        return min(r.position_size(ctx) for r in self._risks)
