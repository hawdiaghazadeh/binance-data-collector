"""Phase 18 paper trading tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from quant_platform.core.context import PipelineContext
from quant_platform.core.manager import PluginManager
from quant_platform.paper_trading.pipeline import PaperTradingPipelineBuilder, register_paper_trading_plugins
from quant_platform.paper_trading.session import PaperTradingSessionEngine, run_paper_session
from quant_platform.paper_trading.source import session_config
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


class TestPaperTradingCompute:
    def test_run_paper_session(self):
        result = run_paper_session(
            session_config(
                strategy=_BuyOnceStrategy(),
                bars=_rising_bars(5),
                fee_rate=0.0,
                slippage_bps=0.0,
                risk_fraction=1.0,
            )
        )
        assert result["status"] == "stopped"
        assert result["trades"] == 1
        assert result["pnl"] > 0
        assert len(result["equity_curve"]) == 5

    def test_paper_session_start_stop(self):
        engine = PaperTradingSessionEngine(
            strategy=_BuyOnceStrategy(),
            bars=_rising_bars(4),
            fee_rate=0.0,
            slippage_bps=0.0,
            risk_fraction=1.0,
        )
        engine.start()
        result = engine.stop()
        assert result["trades"] == 1
        assert "portfolio_state" in result


class TestPaperTradingRegistry:
    def test_paper_engine_plugin(self):
        manager = PluginManager()
        register_paper_trading_plugins(manager)
        engine = manager.get(
            "platform.paper_trading",
            "paper_engine",
            config=session_config(
                strategy=_BuyOnceStrategy(),
                bars=_rising_bars(4),
                fee_rate=0.0,
                slippage_bps=0.0,
                risk_fraction=1.0,
            ),
        )
        engine.start()
        result = engine.stop()
        assert result["status"] == "stopped"
        assert result["pnl"] > 0

    def test_paper_trading_pipeline_builder(self):
        manager = PluginManager()
        register_paper_trading_plugins(manager)
        builder = PaperTradingPipelineBuilder(manager)
        ctx = PipelineContext()
        result = builder.run(
            ctx,
            strategy=_BuyOnceStrategy(),
            bars=_rising_bars(4),
            fee_rate=0.0,
            slippage_bps=0.0,
            risk_fraction=1.0,
        )
        assert result["trades"] == 1
        assert ctx.require("paper_trading_result").payload == result
        assert "portfolio_state" in ctx.keys()
        assert "equity_curve" in ctx.keys()
