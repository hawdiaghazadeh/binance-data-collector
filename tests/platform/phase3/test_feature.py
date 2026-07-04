"""Phase 3 feature registry tests."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.manager import PluginManager
from quant_platform.features.pipeline import FeaturePipelineBuilder, register_feature_plugins
from quant_platform.plugins.atr_feature import compute_wilder_atr
from quant_platform.plugins.vwap_feature import compute_cumulative_vwap
from services.shared.models import KlineRow


def _sample_klines() -> list[KlineRow]:
    t0 = datetime(2024, 1, 1, tzinfo=timezone.utc)
    t1 = datetime(2024, 1, 1, 1, tzinfo=timezone.utc)
    return [
        KlineRow(
            symbol="BTCUSDT",
            timeframe="1h",
            open_time=t0,
            open=100.0,
            high=110.0,
            low=90.0,
            close=105.0,
            volume=1000.0,
            close_time=t1,
            quote_volume=100000.0,
            trade_count=10,
            taker_buy_volume=500.0,
            taker_buy_quote_volume=50000.0,
        )
    ]


def _multi_klines() -> list[KlineRow]:
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    rows: list[KlineRow] = []
    specs = [
        (100.0, 110.0, 90.0, 105.0, 1000.0),
        (105.0, 115.0, 100.0, 110.0, 2000.0),
        (110.0, 120.0, 105.0, 115.0, 1500.0),
    ]
    for index, (open_, high, low, close, volume) in enumerate(specs):
        open_time = base.replace(hour=index)
        close_time = base.replace(hour=index + 1)
        rows.append(
            KlineRow(
                symbol="BTCUSDT",
                timeframe="1h",
                open_time=open_time,
                open=open_,
                high=high,
                low=low,
                close=close,
                volume=volume,
                close_time=close_time,
                quote_volume=volume * close,
                trade_count=10,
                taker_buy_volume=volume / 2,
                taker_buy_quote_volume=volume * close / 2,
            )
        )
    return rows


class TestFeatureRegistry:
    def test_ohlc_feature(self):
        manager = PluginManager()
        register_feature_plugins(manager)
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="klines", payload=_sample_klines()))
        feature = manager.get("platform.features", "ohlc_feature")
        feature.compute(ctx)
        ohlc = ctx.require("ohlc")
        assert len(ohlc.payload) == 1
        assert ohlc.payload[0]["close"] == 105.0

    def test_volume_feature(self):
        manager = PluginManager()
        register_feature_plugins(manager)
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="klines", payload=_sample_klines()))
        feature = manager.get("platform.features", "volume_feature")
        feature.compute(ctx)
        vol = ctx.require("volume")
        assert vol.payload == [1000.0]

    def test_atr_feature(self):
        manager = PluginManager()
        register_feature_plugins(manager)
        rows = _multi_klines()
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="klines", payload=rows))
        feature = manager.get("platform.features", "atr_feature", config={"period": 2})
        feature.compute(ctx)
        atr = ctx.require("atr")
        assert atr.payload == compute_wilder_atr(rows, period=2)
        assert atr.payload[1] == 17.5
        assert atr.payload[2] == 16.25

    def test_vwap_feature(self):
        manager = PluginManager()
        register_feature_plugins(manager)
        ctx = PipelineContext()
        rows = _multi_klines()
        ctx.emit(DataEnvelope(type_key="klines", payload=rows))
        feature = manager.get("platform.features", "vwap_feature")
        feature.compute(ctx)
        vwap = ctx.require("vwap")
        expected = compute_cumulative_vwap(rows)
        assert vwap.payload == expected
        assert vwap.payload[0] == pytest.approx(101.66666666666666)

    def test_feature_pipeline(self):
        manager = PluginManager()
        register_feature_plugins(manager)
        builder = FeaturePipelineBuilder(manager)
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="klines", payload=_sample_klines()))
        builder.run(ctx, ["ohlc_feature", "volume_feature"])
        assert "ohlc" in ctx.keys()
        assert "volume" in ctx.keys()

    def test_feature_pipeline_with_atr_and_vwap(self):
        manager = PluginManager()
        register_feature_plugins(manager)
        builder = FeaturePipelineBuilder(manager)
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="klines", payload=_multi_klines()))
        builder.run(ctx, ["ohlc_feature", "volume_feature", "atr_feature", "vwap_feature"])
        assert "ohlc" in ctx.keys()
        assert "volume" in ctx.keys()
        assert "atr" in ctx.keys()
        assert "vwap" in ctx.keys()


class TestFeatureHelpers:
    def test_compute_wilder_atr_period_one(self):
        rows = _sample_klines()
        assert compute_wilder_atr(rows, period=1) == [20.0]

    def test_compute_cumulative_vwap_empty(self):
        assert compute_cumulative_vwap([]) == []
