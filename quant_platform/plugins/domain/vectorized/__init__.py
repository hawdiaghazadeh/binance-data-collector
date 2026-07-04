"""Vectorized backtesting plugin (Phase 17)."""

from __future__ import annotations

from typing import Any

from quant_platform.backtesting.vectorized import run_vectorized_backtest
from quant_platform.core.plugin import PluginMetadata

PLUGIN_METADATA = PluginMetadata(
    name="vectorized",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Vectorized position-weight backtest over return series",
    input_types=["strategy", "klines", "bars"],
    output_types=["backtest_result", "equity_curve"],
    registry_group="platform.backtesting",
)


class VectorizedBacktest:
    def __init__(self, *, initial_cash: float = 10_000.0) -> None:
        self._initial_cash = initial_cash

    def run(self, strategy: Any, data: Any) -> dict[str, Any]:
        return run_vectorized_backtest(strategy, data, initial_cash=self._initial_cash)


def factory(
    *,
    initial_cash: float = 10_000.0,
    config: dict | None = None,
    **kwargs,
) -> VectorizedBacktest:
    if config and "initial_cash" in config:
        initial_cash = float(config["initial_cash"])
    return VectorizedBacktest(initial_cash=initial_cash)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
