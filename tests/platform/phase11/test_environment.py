"""Phase 11 environment registry tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.manager import PluginManager
from quant_platform.environments.common import parse_action
from quant_platform.environments.futures import FuturesEnvironmentEngine
from quant_platform.environments.pipeline import bootstrap_environment, register_environment_plugins
from quant_platform.environments.spot import SpotEnvironmentEngine
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


class TestEnvironmentHelpers:
    def test_parse_action_variants(self):
        assert parse_action("buy") == ("buy", 1.0)
        assert parse_action({"side": "sell", "size": 0.5}) == ("sell", 0.5)
        assert parse_action(0.8) == ("buy", 0.8)
        assert parse_action(-0.8) == ("sell", 0.8)


class TestSpotEnvironmentEngine:
    def test_reset_and_buy_hold(self):
        prices = [100.0, 110.0, 120.0]
        env = SpotEnvironmentEngine(prices, initial_cash=1000.0, fee_rate=0.0)
        obs = env.reset()
        assert obs["market"] == "spot"
        assert obs["equity"] == 1000.0

        obs, _, done, _ = env.step("buy")
        assert obs["position"] > 0
        assert obs["price"] == 110.0
        assert done is False

        obs, reward, done, _ = env.step("hold")
        assert obs["price"] == 120.0
        assert reward > 0
        assert done is True

    def test_spot_profit_on_uptrend(self):
        prices = [100.0, 120.0]
        env = SpotEnvironmentEngine(prices, initial_cash=1000.0, fee_rate=0.0)
        env.reset()
        env.step("buy")
        _, reward, done, _ = env.step("hold")
        assert reward > 0
        assert done is True


class TestFuturesEnvironmentEngine:
    def test_futures_long_profit(self):
        prices = [100.0, 120.0]
        env = FuturesEnvironmentEngine(prices, initial_margin=1000.0, leverage=2.0, fee_rate=0.0)
        env.reset()
        env.step("buy")
        _, reward, done, info = env.step("hold")
        assert reward > 0
        assert info["leverage"] == 2.0
        assert done is True

    def test_futures_short_profit(self):
        prices = [100.0, 80.0]
        env = FuturesEnvironmentEngine(prices, initial_margin=1000.0, leverage=2.0, fee_rate=0.0)
        env.reset()
        env.step("sell")
        _, reward, _, _ = env.step("hold")
        assert reward > 0


class TestEnvironmentRegistry:
    def test_spot_env_plugin(self):
        manager = PluginManager()
        register_environment_plugins(manager)
        env = manager.get(
            "platform.environments",
            "spot_env",
            config={"prices": [100.0, 110.0, 120.0], "initial_cash": 1000.0, "fee_rate": 0.0},
        )
        obs = env.reset()
        assert obs["market"] == "spot"
        obs, _, _, _ = env.step("buy")
        assert obs["price"] == 110.0
        obs, reward, done, _ = env.step("hold")
        assert obs["price"] == 120.0
        assert reward > 0
        assert done is True

    def test_futures_env_plugin(self):
        manager = PluginManager()
        register_environment_plugins(manager)
        env = manager.get(
            "platform.environments",
            "futures_env",
            config={"prices": [100.0, 90.0, 80.0], "initial_margin": 1000.0, "leverage": 3.0, "fee_rate": 0.0},
        )
        env.reset()
        _, reward, _, info = env.step("sell")
        assert info["leverage"] == 3.0
        assert isinstance(reward, float)

    def test_bootstrap_from_klines_context(self):
        manager = PluginManager()
        ctx = PipelineContext()
        ctx.emit(
            DataEnvelope(
                type_key="klines",
                payload=[_kline_row(close=100.0, index=0), _kline_row(close=105.0, index=1)],
            )
        )
        env = bootstrap_environment(manager, "spot_env", ctx, initial_cash=500.0, fee_rate=0.0)
        obs = env.reset()
        assert obs["price"] == 100.0
        obs, _, done, _ = env.step("hold")
        assert obs["price"] == 105.0
        assert done is True

    def test_invalid_prices_raises(self):
        with pytest.raises(ValueError, match="prices must not be empty"):
            SpotEnvironmentEngine([])
