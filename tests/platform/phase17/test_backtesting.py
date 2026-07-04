"""Phase 17 backtesting tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from quant_platform.backtesting.event_driven import run_event_driven_backtest
from quant_platform.backtesting.pipeline import BacktestPipelineBuilder, register_backtesting_plugins
from quant_platform.backtesting.vectorized import run_vectorized_backtest
from quant_platform.core.context import PipelineContext
from quant_platform.core.manager import PluginManager
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


def _rising_bars(count: int) -> list[KlineRow]:
    return [_kline_row(close=100.0 + index, index=index) for index in range(count)]


class _BuyOnceStrategy:
    def __init__(self) -> None:
        self._bought = False

    def on_bar(self, ctx) -> None:
        return None

    def signals(self, ctx) -> list[dict]:
        if not self._bought:
            self._bought = True
            return [{"side": "buy", "size": 1.0}]
        return [{"side": "hold", "size": 0.0}]


class _BuyHoldWeights:
    def positions(self, bars: list) -> list[float]:
        return [1.0 for _ in bars]


class TestBacktestingCompute:
    def test_event_driven_backtest_buy_once(self):
        result = run_event_driven_backtest(
            _BuyOnceStrategy(),
            _rising_bars(5),
            initial_cash=10_000.0,
            fee_rate=0.0,
        )
        assert result["method"] == "event_driven"
        assert result["trades"] == 1
        assert result["pnl"] > 0
        assert len(result["equity_curve"]) == 6

    def test_vectorized_backtest_buy_hold(self):
        result = run_vectorized_backtest(
            _BuyHoldWeights(),
            _rising_bars(5),
            initial_cash=10_000.0,
        )
        assert result["method"] == "vectorized"
        assert result["pnl"] > 0
        assert result["final_equity"] > 10_000.0


class TestBacktestingRegistry:
    def test_event_driven_plugin(self):
        manager = PluginManager()
        register_backtesting_plugins(manager)
        engine = manager.get("platform.backtesting", "event_driven", config={"fee_rate": 0.0})
        result = engine.run(_BuyOnceStrategy(), _rising_bars(4))
        assert result["trades"] == 1
        assert "max_drawdown" in result

    def test_vectorized_plugin(self):
        manager = PluginManager()
        register_backtesting_plugins(manager)
        engine = manager.get("platform.backtesting", "vectorized")
        result = engine.run(_BuyHoldWeights(), _rising_bars(4))
        assert result["pnl"] > 0

    def test_backtest_pipeline_builder(self):
        manager = PluginManager()
        register_backtesting_plugins(manager)
        builder = BacktestPipelineBuilder(manager)
        ctx = PipelineContext()
        result = builder.run(ctx, _BuyOnceStrategy(), _rising_bars(4), engine_name="event_driven")
        assert result["pnl"] > 0
        assert ctx.require("backtest_result").payload == result
        assert "equity_curve" in ctx.keys()
