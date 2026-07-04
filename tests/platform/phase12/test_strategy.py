"""Phase 12 strategy registry tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from quant_platform.composite.strategy import CompositeStrategy
from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.manager import PluginManager
from quant_platform.indicators.compute import compute_ema
from quant_platform.strategies.pipeline import StrategyPipelineBuilder, register_strategy_plugins
from quant_platform.strategies.rules import evaluate_rule_signals
from quant_platform.strategies.smc import evaluate_smc_signals
from services.shared.models import KlineRow


def _kline_row(*, close: float, index: int = 0) -> KlineRow:
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    open_time = base + timedelta(hours=index)
    close_time = base + timedelta(hours=index + 1)
    return KlineRow(
        symbol="BTCUSDT",
        timeframe="1h",
        open_time=open_time,
        open=close - 1,
        high=close + 1,
        low=close - 2,
        close=close,
        volume=1000.0,
        close_time=close_time,
        quote_volume=close * 1000,
        trade_count=10,
        taker_buy_volume=500.0,
        taker_buy_quote_volume=25000.0,
    )


def _rising_closes(count: int) -> list[KlineRow]:
    return [_kline_row(close=100.0 + index, index=index) for index in range(count)]


class TestStrategyCompute:
    def test_evaluate_rule_signals_rsi_oversold(self):
        closes = [float(100 + index) for index in range(20)]
        rsi = [None] * 19 + [25.0]
        signals = evaluate_rule_signals(closes, rsi=rsi, rsi_oversold=30.0)
        assert any(signal["reason"] == "rsi_oversold" for signal in signals)

    def test_evaluate_rule_signals_ema_cross_up(self):
        closes = [100.0] * 9 + [125.0]
        signals = evaluate_rule_signals(closes, fast_period=3, slow_period=5)
        assert any(signal["reason"] == "ema_cross_up" for signal in signals)

    def test_evaluate_smc_signals(self):
        signals = evaluate_smc_signals(
            market_structure={
                "bos": [{"index": 5, "kind": "bullish_bos", "level": 110.0}],
                "choch": [],
            },
            fvg=[{"index": 5, "direction": "bullish", "top": 112.0, "bottom": 110.0}],
            order_blocks=[],
            current_index=5,
        )
        reasons = {signal["reason"] for signal in signals}
        assert "bullish_bos" in reasons
        assert "fvg" in reasons


class TestStrategyRegistry:
    def test_rule_based_plugin(self):
        manager = PluginManager()
        register_strategy_plugins(manager)
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="klines", payload=_rising_closes(20)))
        ctx.emit(DataEnvelope(type_key="rsi", payload=[None] * 19 + [25.0]))
        strategy = manager.get("platform.strategies", "rule_based")
        strategy.on_bar(ctx)
        signals = strategy.signals(ctx)
        assert any(signal["side"] == "buy" for signal in signals)
        assert "strategy_signals" in ctx.keys()

    def test_smc_ict_plugin(self):
        manager = PluginManager()
        register_strategy_plugins(manager)
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="klines", payload=_rising_closes(6)))
        ctx.emit(
            DataEnvelope(
                type_key="market_structure",
                payload={"bos": [{"index": 5, "kind": "bullish_bos", "level": 110.0}], "choch": []},
            )
        )
        strategy = manager.get("platform.strategies", "smc_ict")
        strategy.on_bar(ctx)
        signals = strategy.signals(ctx)
        assert signals[0]["source"] == "smc_ict"
        assert signals[0]["side"] == "buy"

    def test_strategy_pipeline(self):
        manager = PluginManager()
        register_strategy_plugins(manager)
        builder = StrategyPipelineBuilder(manager)
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="klines", payload=_rising_closes(20)))
        ctx.emit(DataEnvelope(type_key="rsi", payload=[None] * 19 + [25.0]))
        ctx.emit(
            DataEnvelope(
                type_key="market_structure",
                payload={"bos": [{"index": 19, "kind": "bullish_bos", "level": 119.0}], "choch": []},
            )
        )
        merged = builder.run(ctx, ["rule_based", "smc_ict"])
        assert len(merged) >= 2
        assert ctx.require("strategy_signals").payload == merged

    def test_composite_strategy_with_production_plugins(self):
        manager = PluginManager()
        register_strategy_plugins(manager)
        rule = manager.get("platform.strategies", "rule_based")
        smc = manager.get("platform.strategies", "smc_ict")
        composite = CompositeStrategy([(rule, 1.0), (smc, 0.5)])

        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="klines", payload=_rising_closes(20)))
        ctx.emit(DataEnvelope(type_key="rsi", payload=[None] * 19 + [25.0]))
        ctx.emit(
            DataEnvelope(
                type_key="market_structure",
                payload={"bos": [{"index": 19, "kind": "bearish_bos", "level": 90.0}], "choch": []},
            )
        )
        composite.on_bar(ctx)
        signals = composite.signals(ctx)
        assert any(item.get("weight") == 1.0 for item in signals)
        assert any(item.get("weight") == 0.5 for item in signals)

    def test_rule_based_with_precomputed_ema(self):
        closes = [float(100 + index) for index in range(10)]
        ema = compute_ema(closes, 3)
        signals = evaluate_rule_signals(closes, ema=ema, fast_period=3, slow_period=5)
        assert isinstance(signals, list)
