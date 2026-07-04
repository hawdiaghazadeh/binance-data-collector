"""Phase 5 indicator registry tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.manager import PluginManager
from quant_platform.features.pipeline import FeaturePipelineBuilder, register_feature_plugins
from quant_platform.indicators.compute import compute_ema, compute_macd, compute_rsi
from quant_platform.indicators.pipeline import IndicatorPipelineBuilder, register_indicator_plugins
from quant_platform.indicators.source import fetch_klines_from_storage, resolve_closes
from services.shared.models import KlineRow


def _kline_row(*, close: float, index: int = 0, symbol: str = "BTCUSDT", timeframe: str = "1h") -> KlineRow:
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    open_time = base + timedelta(hours=index)
    close_time = base + timedelta(hours=index + 1)
    return KlineRow(
        symbol=symbol,
        timeframe=timeframe,
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


def _series(closes: list[float]) -> list[KlineRow]:
    return [_kline_row(close=close, index=index) for index, close in enumerate(closes)]


class TestIndicatorCompute:
    def test_compute_ema(self):
        result = compute_ema([1.0, 2.0, 3.0], period=2)
        assert result == [None, 1.5, 2.5]

    def test_compute_rsi_uptrend(self):
        result = compute_rsi([100.0, 110.0, 121.0], period=2)
        assert result[0] is None
        assert result[1] is None
        assert result[2] == 100.0

    def test_compute_macd(self):
        closes = [float(value) for value in range(1, 41)]
        macd_line, signal_line, histogram = compute_macd(closes, fast=3, slow=5, signal=2)
        assert macd_line[4] is not None
        assert signal_line[5] is not None
        assert histogram[5] == pytest.approx(macd_line[5] - signal_line[5])


class TestIndicatorRegistry:
    def test_ema_indicator_from_klines(self):
        manager = PluginManager()
        register_indicator_plugins(manager)
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="klines", payload=_series([10.0, 11.0, 12.0, 13.0])))
        indicator = manager.get("platform.indicators", "ema_indicator", config={"period": 3})
        indicator.compute(ctx)
        ema = ctx.require("ema")
        assert ema.payload[2] == pytest.approx(11.0)
        assert ema.payload[3] == pytest.approx(12.0)

    def test_rsi_indicator(self):
        manager = PluginManager()
        register_indicator_plugins(manager)
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="klines", payload=_series([100.0, 110.0, 121.0])))
        indicator = manager.get("platform.indicators", "rsi_indicator", config={"period": 2})
        indicator.compute(ctx)
        rsi = ctx.require("rsi")
        assert rsi.payload[2] == 100.0

    def test_macd_indicator(self):
        manager = PluginManager()
        register_indicator_plugins(manager)
        ctx = PipelineContext()
        closes = [float(value) for value in range(1, 41)]
        ctx.emit(DataEnvelope(type_key="klines", payload=_series(closes)))
        indicator = manager.get(
            "platform.indicators",
            "macd_indicator",
            config={"fast": 3, "slow": 5, "signal": 2},
        )
        indicator.compute(ctx)
        macd = ctx.require("macd")
        assert macd.payload["macd"][4] is not None
        assert macd.payload["signal"][5] is not None

    def test_indicator_pipeline(self):
        manager = PluginManager()
        register_indicator_plugins(manager)
        builder = IndicatorPipelineBuilder(manager)
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="klines", payload=_series([1.0, 2.0, 3.0, 4.0, 5.0])))
        builder.run(ctx, ["ema_indicator", "rsi_indicator"])
        assert "ema" in ctx.keys()
        assert "rsi" in ctx.keys()

    def test_feature_then_indicator_pipeline(self):
        manager = PluginManager()
        register_feature_plugins(manager)
        register_indicator_plugins(manager)
        feature_builder = FeaturePipelineBuilder(manager)
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="klines", payload=_series([10.0, 11.0, 12.0, 13.0])))
        feature_builder.run(ctx, ["ohlc_feature"])
        indicator = manager.get("platform.indicators", "ema_indicator", config={"period": 3})
        indicator.compute(ctx)
        ema = ctx.require("ema")
        assert ema.payload[2] == pytest.approx(11.0)


class TestClickHouseIndicatorSource:
    def test_fetch_klines_from_storage(self):
        backend = MagicMock()
        rows = _series([100.0, 101.0, 102.0])
        backend.fetch_klines.return_value = rows
        result = fetch_klines_from_storage(
            backend,
            symbol="BTCUSDT",
            timeframe="1h",
            limit=3,
        )
        assert result == rows
        backend.fetch_klines.assert_called_once_with(symbol="BTCUSDT", timeframe="1h", limit=3)

    def test_indicator_query_loads_from_storage_backend(self):
        backend = MagicMock()
        rows = _series([10.0, 11.0, 12.0, 13.0])
        backend.fetch_klines.return_value = rows
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="storage_backend", payload=backend))
        ctx.emit(
            DataEnvelope(
                type_key="indicator_query",
                payload={"symbol": "BTCUSDT", "timeframe": "1h", "limit": 4},
            )
        )
        closes = resolve_closes(ctx)
        assert closes == [10.0, 11.0, 12.0, 13.0]

    def test_indicator_from_clickhouse_context(self):
        manager = PluginManager()
        register_indicator_plugins(manager)
        backend = MagicMock()
        backend.fetch_klines.return_value = _series([10.0, 11.0, 12.0, 13.0])
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="storage_backend", payload=backend))
        ctx.emit(
            DataEnvelope(
                type_key="indicator_query",
                payload={"symbol": "BTCUSDT", "timeframe": "1h", "limit": 4},
            )
        )
        indicator = manager.get("platform.indicators", "ema_indicator", config={"period": 3})
        indicator.compute(ctx)
        ema = ctx.require("ema")
        assert ema.payload[3] == pytest.approx(12.0)
