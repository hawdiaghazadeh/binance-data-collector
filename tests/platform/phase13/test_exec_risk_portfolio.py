"""Phase 13 execution + risk + portfolio tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from quant_platform.composite.risk import CompositeRisk
from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.manager import PluginManager
from quant_platform.executions.simulation import simulate_fill
from quant_platform.order_flow.pipeline import OrderFlowPipelineBuilder, register_order_flow_plugins
from quant_platform.portfolios.multi import MultiAssetPortfolioEngine
from quant_platform.portfolios.single import SingleAssetPortfolioEngine
from quant_platform.risks.fixed import check_fixed_risk, fixed_position_size
from quant_platform.risks.kelly import compute_kelly_fraction, kelly_position_size
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


class TestOrderFlowCompute:
    def test_simulate_fill_buy(self):
        fill = simulate_fill(
            {"symbol": "BTCUSDT", "side": "buy", "size": 0.1},
            price=100.0,
            equity=10_000.0,
            fee_rate=0.001,
            slippage_bps=0.0,
        )
        assert fill["status"] == "filled"
        assert fill["quantity"] == pytest.approx(10.0)
        assert fill["fee"] == pytest.approx(1.0)

    def test_fixed_position_size(self):
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="equity", payload=10_000.0))
        assert fixed_position_size(ctx, risk_fraction=0.05) == 0.05

    def test_compute_kelly_fraction(self):
        assert compute_kelly_fraction(0.6, 2.0, cap=0.5) == pytest.approx(0.4)
        assert compute_kelly_fraction(0.4, 1.0, cap=0.25) == pytest.approx(0.0)

    def test_single_asset_portfolio_apply_fill(self):
        engine = SingleAssetPortfolioEngine(initial_cash=10_000.0)
        fill = simulate_fill(
            {"symbol": "BTCUSDT", "side": "buy", "size": 0.5},
            price=100.0,
            equity=10_000.0,
            slippage_bps=0.0,
            fee_rate=0.0,
        )
        state = engine.apply_fill(fill, price=100.0)
        assert state["positions"]["BTCUSDT"]["quantity"] == pytest.approx(50.0)
        assert state["cash"] == pytest.approx(5_000.0)

    def test_multi_asset_portfolio_two_symbols(self):
        engine = MultiAssetPortfolioEngine(initial_cash=10_000.0)
        btc_fill = simulate_fill(
            {"symbol": "BTCUSDT", "side": "buy", "size": 0.25},
            price=100.0,
            equity=10_000.0,
            slippage_bps=0.0,
            fee_rate=0.0,
        )
        engine.apply_fill(btc_fill, prices={"BTCUSDT": 100.0, "ETHUSDT": 50.0})
        eth_fill = simulate_fill(
            {"symbol": "ETHUSDT", "side": "buy", "size": 0.25},
            price=50.0,
            equity=engine.state(prices={"BTCUSDT": 100.0, "ETHUSDT": 50.0})["equity"],
            slippage_bps=0.0,
            fee_rate=0.0,
        )
        state = engine.apply_fill(eth_fill, prices={"BTCUSDT": 100.0, "ETHUSDT": 50.0})
        assert "BTCUSDT" in state["positions"]
        assert "ETHUSDT" in state["positions"]


class TestOrderFlowRegistry:
    def test_simulation_execution_plugin(self):
        manager = PluginManager()
        register_order_flow_plugins(manager)
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="price", payload=100.0))
        ctx.emit(DataEnvelope(type_key="equity", payload=10_000.0))
        execution = manager.get("platform.executions", "simulation_execution")
        fill = execution.execute_order(ctx, {"side": "buy", "size": 0.1})
        assert fill["status"] == "filled"
        assert "execution_result" in ctx.keys()

    def test_fixed_risk_plugin(self):
        manager = PluginManager()
        register_order_flow_plugins(manager)
        ctx = PipelineContext()
        ctx.emit(
            DataEnvelope(
                type_key="portfolio_state",
                payload={"equity": 10_000.0, "exposure": 0.0, "cash": 10_000.0, "positions": {}},
            )
        )
        risk = manager.get("platform.risks", "fixed_risk", config={"risk_fraction": 0.03})
        assert risk.position_size(ctx) == 0.03
        assert risk.check(ctx, {"side": "buy", "size": 0.03}) is True
        assert check_fixed_risk(ctx, {"side": "buy", "size": 0.5}, max_exposure=0.1) is False

    def test_kelly_risk_plugin(self):
        manager = PluginManager()
        register_order_flow_plugins(manager)
        ctx = PipelineContext()
        ctx.emit(
            DataEnvelope(
                type_key="trade_stats",
                payload={"win_rate": 0.55, "win_loss_ratio": 1.5},
            )
        )
        risk = manager.get("platform.risks", "kelly_risk")
        size = risk.position_size(ctx)
        assert size == pytest.approx(kelly_position_size(ctx))
        assert risk.check(ctx, {"side": "buy", "size": size}) is True

    def test_single_asset_plugin(self):
        manager = PluginManager()
        register_order_flow_plugins(manager)
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="price", payload=100.0))
        ctx.emit(
            DataEnvelope(
                type_key="execution_result",
                payload=simulate_fill(
                    {"symbol": "BTCUSDT", "side": "buy", "size": 0.2},
                    price=100.0,
                    equity=10_000.0,
                    slippage_bps=0.0,
                    fee_rate=0.0,
                ),
            )
        )
        portfolio = manager.get("platform.portfolios", "single_asset")
        portfolio.update(ctx)
        state = ctx.require("portfolio_state").payload
        assert state["positions"]["BTCUSDT"]["quantity"] == pytest.approx(20.0)

    def test_order_flow_pipeline(self):
        manager = PluginManager()
        register_order_flow_plugins(manager)
        builder = OrderFlowPipelineBuilder(manager)
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="klines", payload=[_kline_row(close=100.0)]))
        ctx.emit(
            DataEnvelope(
                type_key="portfolio_state",
                payload={"equity": 10_000.0, "exposure": 0.0, "cash": 10_000.0, "positions": {}},
            )
        )
        fill = builder.process_order(ctx, {"side": "buy", "symbol": "BTCUSDT"})
        assert fill["status"] == "filled"
        assert "portfolio_state" in ctx.keys()
        assert "step_pnl" in ctx.keys()

    def test_composite_risk_with_production_plugins(self):
        manager = PluginManager()
        register_order_flow_plugins(manager)
        fixed = manager.get("platform.risks", "fixed_risk", config={"risk_fraction": 0.05})
        kelly = manager.get("platform.risks", "kelly_risk")
        composite = CompositeRisk([fixed, kelly])

        ctx = PipelineContext()
        ctx.emit(
            DataEnvelope(
                type_key="portfolio_state",
                payload={"equity": 10_000.0, "exposure": 0.0, "cash": 10_000.0, "positions": {}},
            )
        )
        ctx.emit(
            DataEnvelope(
                type_key="trade_stats",
                payload={"win_rate": 0.55, "win_loss_ratio": 1.5},
            )
        )
        size = composite.position_size(ctx)
        assert size == min(fixed.position_size(ctx), kelly.position_size(ctx))
        assert composite.check(ctx, {"side": "buy", "size": size}) is True
