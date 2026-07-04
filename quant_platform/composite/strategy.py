"""Composable strategy ensemble."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import PipelineContext
from quant_platform.interfaces.domain import StrategyProtocol


class CompositeStrategy:
    """Run multiple strategies and merge their signals."""

    def __init__(self, strategies: list[tuple[StrategyProtocol, float]]) -> None:
        self._strategies = strategies

    def on_bar(self, ctx: PipelineContext) -> None:
        for strategy, _weight in self._strategies:
            strategy.on_bar(ctx)

    def signals(self, ctx: PipelineContext) -> list[Any]:
        merged: list[Any] = []
        for strategy, weight in self._strategies:
            if weight <= 0:
                continue
            for signal in strategy.signals(ctx):
                if isinstance(signal, dict):
                    merged.append({**signal, "weight": weight})
                else:
                    merged.append({"signal": signal, "weight": weight})
        return merged
