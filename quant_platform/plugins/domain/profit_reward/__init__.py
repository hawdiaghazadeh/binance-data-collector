"""Profit reward plugin (Phase 9)."""

from __future__ import annotations

from quant_platform.core.context import PipelineContext
from quant_platform.core.plugin import PluginMetadata
from quant_platform.rewards.profit import calculate_profit_reward

PLUGIN_METADATA = PluginMetadata(
    name="profit_reward",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Step PnL reward from pnl or portfolio_state context",
    input_types=["pnl", "step_pnl", "portfolio_state"],
    output_types=["reward"],
    registry_group="platform.rewards",
)


class ProfitReward:
    def calculate(self, ctx: PipelineContext) -> float:
        return calculate_profit_reward(ctx)


def factory(**kwargs) -> ProfitReward:
    return ProfitReward()


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
