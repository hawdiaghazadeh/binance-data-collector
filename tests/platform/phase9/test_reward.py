"""Phase 9 reward registry tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from quant_platform.composite.reward import CompositeReward
from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.manager import PluginManager
from quant_platform.rewards.drawdown import calculate_drawdown_penalty, compute_current_drawdown, compute_max_drawdown
from quant_platform.rewards.pipeline import RewardPipelineBuilder, register_reward_plugins
from quant_platform.rewards.profit import calculate_profit_reward
from quant_platform.rewards.sharpe import calculate_sharpe_reward, compute_sharpe_ratio
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


class TestRewardCompute:
    def test_calculate_profit_reward(self):
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="step_pnl", payload=125.5))
        assert calculate_profit_reward(ctx) == 125.5

    def test_compute_sharpe_ratio(self):
        returns = [0.01, 0.02, -0.005, 0.015, 0.0]
        expected = compute_sharpe_ratio(returns)
        assert expected == pytest.approx(0.7715885154726594)

    def test_calculate_sharpe_reward_window(self):
        returns = [0.01, 0.02, -0.01, 0.03, 0.015, 0.005]
        value = calculate_sharpe_reward(returns, window=3)
        assert value == pytest.approx(compute_sharpe_ratio(returns[-3:]), rel=1e-6)

    def test_drawdown_metrics(self):
        equity = [10000.0, 11000.0, 9500.0]
        assert compute_max_drawdown(equity) == pytest.approx(1500.0 / 11000.0)
        assert compute_current_drawdown(equity) == pytest.approx(1500.0 / 11000.0)
        assert calculate_drawdown_penalty(equity, penalty_factor=2.0) == pytest.approx(-3000.0 / 11000.0)


class TestRewardRegistry:
    def test_profit_reward_plugin(self):
        manager = PluginManager()
        register_reward_plugins(manager)
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="pnl", payload=50.0))
        reward = manager.get("platform.rewards", "profit_reward")
        assert reward.calculate(ctx) == 50.0

    def test_sharpe_reward_plugin(self):
        manager = PluginManager()
        register_reward_plugins(manager)
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="returns", payload=[0.01, 0.02, -0.005, 0.015]))
        reward = manager.get("platform.rewards", "sharpe_reward", config={"window": 4})
        assert reward.calculate(ctx) == pytest.approx(compute_sharpe_ratio([0.01, 0.02, -0.005, 0.015]))

    def test_sharpe_reward_from_klines(self):
        manager = PluginManager()
        register_reward_plugins(manager)
        rows = [_kline_row(close=close, index=index) for index, close in enumerate([100.0, 110.0, 105.0, 115.0])]
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="klines", payload=rows))
        reward = manager.get("platform.rewards", "sharpe_reward", config={"window": 3})
        assert reward.calculate(ctx) != 0.0

    def test_drawdown_penalty_plugin(self):
        manager = PluginManager()
        register_reward_plugins(manager)
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="equity_curve", payload=[10000.0, 11000.0, 9500.0]))
        reward = manager.get("platform.rewards", "drawdown_penalty", config={"penalty_factor": 1.0})
        assert reward.calculate(ctx) == pytest.approx(-1500.0 / 11000.0)

    def test_reward_pipeline(self):
        manager = PluginManager()
        register_reward_plugins(manager)
        builder = RewardPipelineBuilder(manager)
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="step_pnl", payload=100.0))
        ctx.emit(DataEnvelope(type_key="equity_curve", payload=[10000.0, 11000.0, 9500.0]))
        ctx.emit(DataEnvelope(type_key="returns", payload=[0.01, 0.02, -0.005, 0.015]))
        total = builder.run(
            ctx,
            ["profit_reward", "sharpe_reward", "drawdown_penalty"],
            weights=[1.0, 0.5, 1.0],
        )
        payload = ctx.require("reward").payload
        assert payload["components"]["profit_reward"] == 100.0
        assert total == pytest.approx(
            100.0 + 0.5 * payload["components"]["sharpe_reward"] + payload["components"]["drawdown_penalty"]
        )

    def test_composite_reward_with_production_plugins(self):
        manager = PluginManager()
        register_reward_plugins(manager)
        profit = manager.get("platform.rewards", "profit_reward")
        drawdown = manager.get("platform.rewards", "drawdown_penalty", config={"penalty_factor": 1.0})
        composite = CompositeReward([(profit, 1.0), (drawdown, 2.0)])

        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="step_pnl", payload=10.0))
        ctx.emit(DataEnvelope(type_key="equity_curve", payload=[10000.0, 11000.0, 9900.0]))
        expected_penalty = calculate_drawdown_penalty([10000.0, 11000.0, 9900.0], penalty_factor=1.0)
        assert composite.calculate(ctx) == pytest.approx(10.0 + 2.0 * expected_penalty)
