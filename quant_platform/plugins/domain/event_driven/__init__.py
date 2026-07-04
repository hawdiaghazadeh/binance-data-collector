"""Event-driven backtesting plugin (Phase 17)."""

from __future__ import annotations

from typing import Any

from quant_platform.backtesting.event_driven import run_event_driven_backtest
from quant_platform.core.plugin import PluginMetadata

PLUGIN_METADATA = PluginMetadata(
    name="event_driven",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Bar-by-bar event-driven backtest over strategy signals",
    input_types=["strategy", "klines", "bars"],
    output_types=["backtest_result", "equity_curve"],
    registry_group="platform.backtesting",
)


class EventDrivenBacktest:
    def __init__(
        self,
        *,
        initial_cash: float = 10_000.0,
        fee_rate: float = 0.001,
    ) -> None:
        self._initial_cash = initial_cash
        self._fee_rate = fee_rate

    def run(self, strategy: Any, data: Any) -> dict[str, Any]:
        return run_event_driven_backtest(
            strategy,
            data,
            initial_cash=self._initial_cash,
            fee_rate=self._fee_rate,
        )


def factory(
    *,
    initial_cash: float = 10_000.0,
    fee_rate: float = 0.001,
    config: dict | None = None,
    **kwargs,
) -> EventDrivenBacktest:
    if config:
        initial_cash = float(config.get("initial_cash", initial_cash))
        fee_rate = float(config.get("fee_rate", fee_rate))
    return EventDrivenBacktest(initial_cash=initial_cash, fee_rate=fee_rate)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
