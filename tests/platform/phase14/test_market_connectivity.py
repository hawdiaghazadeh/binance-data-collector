"""Phase 14 exchange + broker tests."""

from __future__ import annotations

import httpx
import pytest
import respx

from quant_platform.brokers.paper import PaperBrokerEngine
from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.manager import PluginManager
from quant_platform.exchanges.binance import BinanceRestClient
from quant_platform.exchanges.parse import parse_binance_klines
from quant_platform.market_connectivity.pipeline import (
    MarketConnectivityPipelineBuilder,
    register_market_connectivity_plugins,
)


SAMPLE_KLINE = [
    [
        1704067200000,
        "42000.0",
        "42500.0",
        "41800.0",
        "42300.0",
        "100.5",
        1704070799999,
        "4230000.0",
        1200,
        "50.0",
        "2100000.0",
        "0",
    ]
]


class TestExchangeCompute:
    @respx.mock
    def test_binance_fetch_ticker(self):
        respx.get("https://fapi.binance.com/fapi/v1/ticker/price").mock(
            return_value=httpx.Response(200, json={"symbol": "BTCUSDT", "price": "50000.00"})
        )
        client = BinanceRestClient()
        ticker = client.fetch_ticker_price("BTCUSDT")
        assert ticker == {"symbol": "BTCUSDT", "price": 50000.0}
        client.close()

    @respx.mock
    def test_binance_fetch_klines(self):
        respx.get("https://fapi.binance.com/fapi/v1/klines").mock(
            return_value=httpx.Response(200, json=SAMPLE_KLINE)
        )
        client = BinanceRestClient()
        raw = client.fetch_klines_raw("BTCUSDT", "1h", limit=1)
        rows = parse_binance_klines(raw, symbol="BTCUSDT", timeframe="1h")
        assert len(rows) == 1
        assert rows[0].close == 42300.0
        client.close()

    def test_paper_broker_submit_buy(self):
        engine = PaperBrokerEngine(slippage_bps=0.0, fee_rate=0.0)
        result = engine.submit_order(
            {"symbol": "BTCUSDT", "side": "buy", "size": 0.1},
            price=100.0,
            equity=10_000.0,
        )
        assert result["status"] == "filled"
        assert result["fill"]["quantity"] == pytest.approx(10.0)

    def test_paper_broker_cancel(self):
        engine = PaperBrokerEngine()
        submit = engine.submit_order({"side": "hold"}, price=100.0)
        assert engine.cancel_order(submit["order_id"]) is True
        assert engine.cancel_order("missing") is False


class TestMarketConnectivityRegistry:
    @respx.mock
    def test_binance_exchange_plugin(self):
        respx.get("https://fapi.binance.com/fapi/v1/ticker/price").mock(
            return_value=httpx.Response(200, json={"symbol": "BTCUSDT", "price": "51000.00"})
        )
        respx.get("https://fapi.binance.com/fapi/v1/klines").mock(
            return_value=httpx.Response(200, json=SAMPLE_KLINE)
        )

        manager = PluginManager()
        register_market_connectivity_plugins(manager)
        exchange = manager.get("platform.exchanges", "binance_exchange")
        ticker = exchange.fetch_ticker("BTCUSDT")
        candles = exchange.fetch_ohlcv("BTCUSDT", "1h", limit=1)
        assert ticker["price"] == 51000.0
        assert candles[0].symbol == "BTCUSDT"

    def test_paper_broker_plugin(self):
        manager = PluginManager()
        register_market_connectivity_plugins(manager)
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="price", payload=100.0))
        ctx.emit(DataEnvelope(type_key="equity", payload=10_000.0))
        broker = manager.get("platform.brokers", "paper_broker", config={"context": ctx})
        result = broker.submit_order({"side": "buy", "size": 0.1, "symbol": "BTCUSDT"})
        assert result["status"] == "filled"
        assert "broker_result" in ctx.keys()
        assert "execution_result" in ctx.keys()

    @respx.mock
    def test_market_connectivity_pipeline(self):
        respx.get("https://fapi.binance.com/fapi/v1/ticker/price").mock(
            return_value=httpx.Response(200, json={"symbol": "BTCUSDT", "price": "50000.00"})
        )
        respx.get("https://fapi.binance.com/fapi/v1/klines").mock(
            return_value=httpx.Response(200, json=SAMPLE_KLINE)
        )

        manager = PluginManager()
        register_market_connectivity_plugins(manager)
        builder = MarketConnectivityPipelineBuilder(manager)
        ctx = PipelineContext()
        ctx.emit(
            DataEnvelope(
                type_key="portfolio_state",
                payload={"equity": 10_000.0, "exposure": 0.0, "cash": 10_000.0, "positions": {}},
            )
        )
        result = builder.fetch_and_submit(
            ctx,
            "BTCUSDT",
            "1h",
            {"side": "buy", "size": 0.05},
        )
        assert result["status"] == "filled"
        assert ctx.require("price").payload == 50000.0
        assert len(ctx.require("klines").payload) == 1
        assert ctx.require("execution_result").payload["side"] == "buy"

    @respx.mock
    def test_fetch_market_data_emits_context(self):
        respx.get("https://fapi.binance.com/fapi/v1/ticker/price").mock(
            return_value=httpx.Response(200, json={"symbol": "ETHUSDT", "price": "3000.00"})
        )
        respx.get("https://fapi.binance.com/fapi/v1/klines").mock(
            return_value=httpx.Response(200, json=SAMPLE_KLINE)
        )

        manager = PluginManager()
        register_market_connectivity_plugins(manager)
        builder = MarketConnectivityPipelineBuilder(manager)
        ctx = PipelineContext()
        payload = builder.fetch_market_data(ctx, "ETHUSDT", "1h", limit=1)
        assert payload["ticker"]["symbol"] == "ETHUSDT"
        assert "ticker" in ctx.keys()
        assert "klines" in ctx.keys()
