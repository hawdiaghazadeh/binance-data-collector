"""Rule-based strategy plugin (Phase 12)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.plugin import PluginMetadata
from quant_platform.strategies.rules import evaluate_rule_signals
from quant_platform.strategies.source import resolve_closes, resolve_indicator_series

PLUGIN_METADATA = PluginMetadata(
    name="rule_based",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Indicator rule strategy using EMA cross and RSI thresholds",
    input_types=["klines", "ohlc", "ema", "rsi"],
    output_types=["strategy_signals"],
    registry_group="platform.strategies",
)


class RuleBasedStrategy:
    def __init__(
        self,
        fast_period: int = 9,
        slow_period: int = 21,
        rsi_oversold: float = 30.0,
        rsi_overbought: float = 70.0,
    ) -> None:
        self._fast_period = fast_period
        self._slow_period = slow_period
        self._rsi_oversold = rsi_oversold
        self._rsi_overbought = rsi_overbought
        self._last_signals: list[dict[str, Any]] = []

    def on_bar(self, ctx: PipelineContext) -> None:
        self._last_signals = self._evaluate(ctx)
        ctx.emit(DataEnvelope(type_key="strategy_signals", payload=self._last_signals))

    def signals(self, ctx: PipelineContext) -> list[Any]:
        if self._last_signals:
            return list(self._last_signals)
        return self._evaluate(ctx)

    def _evaluate(self, ctx: PipelineContext) -> list[dict[str, Any]]:
        closes = resolve_closes(ctx)
        ema = resolve_indicator_series(ctx, "ema")
        rsi = resolve_indicator_series(ctx, "rsi")
        return evaluate_rule_signals(
            closes,
            ema=ema,
            rsi=rsi,
            fast_period=self._fast_period,
            slow_period=self._slow_period,
            rsi_oversold=self._rsi_oversold,
            rsi_overbought=self._rsi_overbought,
        )


def factory(
    *,
    fast_period: int = 9,
    slow_period: int = 21,
    rsi_oversold: float = 30.0,
    rsi_overbought: float = 70.0,
    config: dict | None = None,
    **kwargs,
) -> RuleBasedStrategy:
    if config:
        fast_period = int(config.get("fast_period", fast_period))
        slow_period = int(config.get("slow_period", slow_period))
        rsi_oversold = float(config.get("rsi_oversold", rsi_oversold))
        rsi_overbought = float(config.get("rsi_overbought", rsi_overbought))
    return RuleBasedStrategy(
        fast_period=fast_period,
        slow_period=slow_period,
        rsi_oversold=rsi_oversold,
        rsi_overbought=rsi_overbought,
    )


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
