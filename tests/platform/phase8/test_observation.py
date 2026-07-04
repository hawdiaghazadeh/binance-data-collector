"""Phase 8 observation registry tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from quant_platform.composite.observation import CompositeObservation
from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.manager import PluginManager
from quant_platform.features.pipeline import FeaturePipelineBuilder, register_feature_plugins
from quant_platform.market_structure.bars import Bar
from quant_platform.observations.candle import build_candle_observation
from quant_platform.observations.pipeline import ObservationPipelineBuilder, register_observation_plugins
from quant_platform.observations.portfolio import build_portfolio_observation
from quant_platform.observations.risk import build_risk_observation
from services.shared.models import KlineRow


def _bar(*, open_: float, high: float, low: float, close: float, index: int = 0) -> Bar:
    return Bar(open=open_, high=high, low=low, close=close, index=index)


def _kline_row(*, open_: float, high: float, low: float, close: float, index: int = 0) -> KlineRow:
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    open_time = base + timedelta(hours=index)
    close_time = base + timedelta(hours=index + 1)
    return KlineRow(
        symbol="BTCUSDT",
        timeframe="1h",
        open_time=open_time,
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=1000.0,
        close_time=close_time,
        quote_volume=close * 1000,
        trade_count=10,
        taker_buy_volume=500.0,
        taker_buy_quote_volume=25000.0,
    )


class TestObservationCompute:
    def test_build_candle_observation(self):
        bars = [
            _bar(open_=100, high=101, low=99, close=100, index=0),
            _bar(open_=100, high=102, low=99, close=101, index=1),
        ]
        observation = build_candle_observation(bars, window=3)
        assert observation["length"] == 2
        assert len(observation["features"]) == 3
        assert observation["features"][-1][3] == pytest.approx(0.0)

    def test_build_portfolio_observation_default(self):
        observation = build_portfolio_observation(PipelineContext())
        assert observation["cash"] == 0.0
        assert observation["positions"] == {}

    def test_build_portfolio_observation_from_context(self):
        ctx = PipelineContext()
        ctx.emit(
            DataEnvelope(
                type_key="portfolio_state",
                payload={
                    "cash": 5000.0,
                    "equity": 12000.0,
                    "positions": {"BTCUSDT": {"size": 0.5}},
                    "exposure": 0.4,
                    "unrealized_pnl": 250.0,
                },
            )
        )
        observation = build_portfolio_observation(ctx)
        assert observation["equity"] == 12000.0
        assert observation["positions"]["BTCUSDT"]["size"] == 0.5

    def test_build_risk_observation(self):
        ctx = PipelineContext()
        ctx.emit(
            DataEnvelope(
                type_key="portfolio_state",
                payload={"exposure": 0.8, "equity": 10000.0, "positions": {}},
            )
        )
        ctx.emit(DataEnvelope(type_key="atr", payload=[None, 12.5]))
        observation = build_risk_observation(ctx, max_exposure=1.0)
        assert observation["exposure"] == 0.8
        assert observation["risk_utilization"] == pytest.approx(0.8)
        assert observation["within_limits"] is True
        assert observation["volatility"] == 12.5


class TestObservationRegistry:
    def test_candle_observation_plugin(self):
        manager = PluginManager()
        register_observation_plugins(manager)
        rows = [
            _kline_row(open_=100, high=101, low=99, close=100, index=0),
            _kline_row(open_=100, high=102, low=99, close=101, index=1),
        ]
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="klines", payload=rows))
        builder = manager.get("platform.observations", "candle_observation", config={"window": 2})
        result = builder.build(ctx)
        assert result["length"] == 2
        assert ctx.require("candle_observation").payload == result

    def test_portfolio_observation_plugin(self):
        manager = PluginManager()
        register_observation_plugins(manager)
        ctx = PipelineContext()
        ctx.emit(
            DataEnvelope(
                type_key="portfolio_state",
                payload={"cash": 1000.0, "equity": 1500.0, "positions": {}, "exposure": 0.2},
            )
        )
        builder = manager.get("platform.observations", "portfolio_observation")
        result = builder.build(ctx)
        assert result["equity"] == 1500.0
        assert "portfolio_observation" in ctx.keys()

    def test_risk_observation_plugin(self):
        manager = PluginManager()
        register_observation_plugins(manager)
        ctx = PipelineContext()
        ctx.emit(
            DataEnvelope(
                type_key="portfolio_state",
                payload={"exposure": 1.2, "equity": 10000.0, "positions": {}},
            )
        )
        builder = manager.get("platform.observations", "risk_observation", config={"max_exposure": 1.0})
        result = builder.build(ctx)
        assert result["within_limits"] is False
        assert result["risk_utilization"] == 1.0

    def test_observation_pipeline(self):
        manager = PluginManager()
        register_observation_plugins(manager)
        pipeline = ObservationPipelineBuilder(manager)
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="klines", payload=[_kline_row(open_=100, high=101, low=99, close=100)]))
        ctx.emit(
            DataEnvelope(
                type_key="portfolio_state",
                payload={"cash": 1000.0, "equity": 1000.0, "positions": {}, "exposure": 0.0},
            )
        )
        pipeline.run(ctx, ["candle_observation", "portfolio_observation", "risk_observation"])
        assert "candle_observation" in ctx.keys()
        assert "portfolio_observation" in ctx.keys()
        assert "risk_observation" in ctx.keys()

    def test_feature_then_candle_observation(self):
        manager = PluginManager()
        register_feature_plugins(manager)
        register_observation_plugins(manager)
        feature_builder = FeaturePipelineBuilder(manager)
        ctx = PipelineContext()
        ctx.emit(
            DataEnvelope(
                type_key="klines",
                payload=[_kline_row(open_=100, high=101, low=99, close=100, index=0)],
            )
        )
        feature_builder.run(ctx, ["ohlc_feature"])
        candle = manager.get("platform.observations", "candle_observation", config={"window": 1})
        candle.build(ctx)
        assert ctx.require("candle_observation").payload["length"] == 1

    def test_composite_observation_with_production_builders(self):
        manager = PluginManager()
        register_observation_plugins(manager)
        candle = manager.get("platform.observations", "candle_observation", config={"window": 1})
        portfolio = manager.get("platform.observations", "portfolio_observation")
        composite = CompositeObservation([(candle, "market"), (portfolio, "portfolio")])

        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="klines", payload=[_kline_row(open_=100, high=101, low=99, close=100)]))
        ctx.emit(
            DataEnvelope(
                type_key="portfolio_state",
                payload={"cash": 500.0, "equity": 500.0, "positions": {}, "exposure": 0.0},
            )
        )
        merged = composite.build(ctx)
        assert "market" in merged
        assert "portfolio" in merged
        assert merged["portfolio"]["cash"] == 500.0
