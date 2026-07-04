"""Phase 19 live trading tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx
import pytest
import respx

from quant_platform.core.context import PipelineContext
from quant_platform.core.manager import PluginManager
from quant_platform.exchanges.binance import BinanceRestClient
from quant_platform.live_trading.pipeline import LiveTradingPipelineBuilder, register_live_trading_plugins
from quant_platform.live_trading.session import LiveTradingSessionEngine, run_live_session
from quant_platform.live_trading.source import live_session_config
from quant_platform.plugins.domain.binance_exchange import BinanceExchange
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


class _MockExchange:
    def __init__(self, prices: list[float]) -> None:
        self._prices = prices
        self._index = 0

    def fetch_ticker(self, symbol: str) -> dict:
        price = self._prices[min(self._index, len(self._prices) - 1)]
        self._index += 1
        return {"symbol": symbol, "price": price}


class TestLiveTradingCompute:
    @respx.mock
    def test_run_live_session_with_exchange(self):
        respx.get("https://fapi.binance.com/fapi/v1/ticker/price").mock(
            return_value=httpx.Response(200, json={"symbol": "BTCUSDT", "price": "50000.00"})
        )
        exchange = BinanceExchange(BinanceRestClient())
        result = run_live_session(
            live_session_config(
                strategy=_BuyOnceStrategy(),
                exchange=exchange,
                fee_rate=0.0,
                slippage_bps=0.0,
                risk_fraction=1.0,
            )
        )
        assert result["mode"] == "live"
        assert result["status"] == "stopped"
        assert result["trades"] == 1

    def test_live_session_replay_bars_with_mock_exchange(self):
        engine = LiveTradingSessionEngine(
            strategy=_BuyOnceStrategy(),
            exchange=_MockExchange([100.0, 101.0, 102.0, 103.0]),
            bars=_rising_bars(4),
            fee_rate=0.0,
            slippage_bps=0.0,
            risk_fraction=1.0,
        )
        engine.start()
        result = engine.stop()
        assert result["trades"] == 1
        assert result["pnl"] > 0
        assert len(result["tickers"]) >= 4


class TestLiveTradingRegistry:
    def test_live_engine_plugin(self):
        manager = PluginManager()
        register_live_trading_plugins(manager)
        exchange = _MockExchange([100.0, 101.0, 102.0, 103.0])
        engine = manager.get(
            "platform.live_trading",
            "live_engine",
            config=live_session_config(
                strategy=_BuyOnceStrategy(),
                exchange=exchange,
                bars=_rising_bars(4),
                fee_rate=0.0,
                slippage_bps=0.0,
                risk_fraction=1.0,
            ),
        )
        engine.start()
        engine.stop()
        assert engine.summary["mode"] == "live"
        assert engine.summary["pnl"] > 0

    def test_live_trading_pipeline_builder(self):
        manager = PluginManager()
        register_live_trading_plugins(manager)
        builder = LiveTradingPipelineBuilder(manager)
        ctx = PipelineContext()
        exchange = _MockExchange([100.0, 101.0, 102.0, 103.0, 104.0])
        result = builder.run(
            ctx,
            strategy=_BuyOnceStrategy(),
            exchange=exchange,
            bars=_rising_bars(5),
            fee_rate=0.0,
            slippage_bps=0.0,
            risk_fraction=1.0,
        )
        assert result["trades"] == 1
        assert ctx.require("live_trading_result").payload == result
        assert "ticker" in ctx.keys()
        assert "portfolio_state" in ctx.keys()
