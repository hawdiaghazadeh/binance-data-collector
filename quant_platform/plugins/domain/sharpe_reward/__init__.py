"""Sharpe ratio reward plugin (Phase 9)."""

from __future__ import annotations

from quant_platform.core.context import PipelineContext
from quant_platform.core.plugin import PluginMetadata
from quant_platform.rewards.sharpe import calculate_sharpe_reward
from quant_platform.rewards.source import resolve_returns

PLUGIN_METADATA = PluginMetadata(
    name="sharpe_reward",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Rolling Sharpe ratio reward from returns or equity curve",
    input_types=["returns", "equity_curve", "klines"],
    output_types=["reward"],
    registry_group="platform.rewards",
)


class SharpeReward:
    def __init__(self, window: int = 20, risk_free: float = 0.0) -> None:
        self._window = window
        self._risk_free = risk_free

    def calculate(self, ctx: PipelineContext) -> float:
        returns = resolve_returns(ctx)
        return calculate_sharpe_reward(returns, window=self._window, risk_free=self._risk_free)


def factory(*, window: int = 20, risk_free: float = 0.0, config: dict | None = None, **kwargs) -> SharpeReward:
    if config:
        window = int(config.get("window", window))
        risk_free = float(config.get("risk_free", risk_free))
    return SharpeReward(window=window, risk_free=risk_free)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
