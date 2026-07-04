"""Phase 3 feature registry tests."""

from __future__ import annotations

from datetime import datetime, timezone

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.manager import PluginManager
from quant_platform.features.pipeline import FeaturePipelineBuilder, register_feature_plugins
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

    def test_feature_pipeline(self):
        manager = PluginManager()
        register_feature_plugins(manager)
        builder = FeaturePipelineBuilder(manager)
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="klines", payload=_sample_klines()))
        builder.run(ctx, ["ohlc_feature", "volume_feature"])
        assert "ohlc" in ctx.keys()
        assert "volume" in ctx.keys()
