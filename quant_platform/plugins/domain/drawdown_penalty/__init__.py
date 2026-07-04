"""Drawdown penalty reward plugin (Phase 9)."""

from __future__ import annotations

from quant_platform.core.context import PipelineContext
from quant_platform.core.plugin import PluginMetadata
from quant_platform.rewards.drawdown import calculate_drawdown_penalty
from quant_platform.rewards.source import resolve_equity_curve

PLUGIN_METADATA = PluginMetadata(
    name="drawdown_penalty",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Negative reward proportional to current equity drawdown",
    input_types=["equity_curve", "portfolio_state"],
    output_types=["reward"],
    registry_group="platform.rewards",
)


class DrawdownPenalty:
    def __init__(self, penalty_factor: float = 1.0) -> None:
        self._penalty_factor = penalty_factor

    def calculate(self, ctx: PipelineContext) -> float:
        equity_curve = resolve_equity_curve(ctx)
        return calculate_drawdown_penalty(equity_curve, penalty_factor=self._penalty_factor)


def factory(*, penalty_factor: float = 1.0, config: dict | None = None, **kwargs) -> DrawdownPenalty:
    if config and "penalty_factor" in config:
        penalty_factor = float(config["penalty_factor"])
    return DrawdownPenalty(penalty_factor=penalty_factor)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
