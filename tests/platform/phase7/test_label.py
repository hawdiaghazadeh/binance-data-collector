"""Phase 7 label registry tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.manager import PluginManager
from quant_platform.features.pipeline import FeaturePipelineBuilder, register_feature_plugins
from quant_platform.labels.direction import compute_direction_labels
from quant_platform.labels.pipeline import LabelPipelineBuilder, register_label_plugins
from quant_platform.labels.regime import compute_regime_labels
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


class TestLabelCompute:
    def test_compute_direction_labels(self):
        closes = [100.0, 105.0, 103.0, 110.0]
        labels = compute_direction_labels(closes, horizon=1, threshold_pct=0.01)
        assert labels[0] == "bullish"
        assert labels[1] == "bearish"
        assert labels[2] == "bullish"
        assert labels[3] is None

    def test_compute_direction_labels_neutral(self):
        closes = [100.0, 100.5, 100.3]
        labels = compute_direction_labels(closes, horizon=1, threshold_pct=0.01)
        assert labels[0] == "neutral"
        assert labels[1] == "neutral"

    def test_compute_regime_labels_trending_bull(self):
        closes = [float(100 + index) for index in range(25)]
        labels = compute_regime_labels(
            closes,
            window=5,
            trend_threshold=0.01,
            volatility_threshold=0.5,
        )
        assert labels[-1] == "trending_bull"

    def test_compute_regime_labels_ranging(self):
        closes = [100.0, 100.1, 99.9, 100.0, 100.05]
        labels = compute_regime_labels(
            closes,
            window=5,
            trend_threshold=0.05,
            volatility_threshold=0.5,
        )
        assert labels[-1] == "ranging"

    def test_compute_regime_labels_high_volatility(self):
        closes = [100.0, 120.0, 90.0, 130.0, 80.0]
        labels = compute_regime_labels(
            closes,
            window=5,
            trend_threshold=0.5,
            volatility_threshold=0.05,
        )
        assert labels[-1] == "high_volatility"


class TestLabelRegistry:
    def test_direction_label_plugin(self):
        manager = PluginManager()
        register_label_plugins(manager)
        rows = [_kline_row(close=close, index=index) for index, close in enumerate([100.0, 105.0, 103.0, 110.0])]
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="klines", payload=rows))
        labeler = manager.get("platform.labels", "direction_label", config={"horizon": 1, "threshold_pct": 0.01})
        labeler.generate(ctx)
        labels = ctx.require("direction_labels")
        assert labels.payload[0] == "bullish"
        assert labels.payload[3] is None

    def test_regime_label_plugin(self):
        manager = PluginManager()
        register_label_plugins(manager)
        closes = [float(100 + index) for index in range(10)]
        rows = [_kline_row(close=close, index=index) for index, close in enumerate(closes)]
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="klines", payload=rows))
        labeler = manager.get(
            "platform.labels",
            "regime_label",
            config={"window": 5, "trend_threshold": 0.01, "volatility_threshold": 0.5},
        )
        labeler.generate(ctx)
        labels = ctx.require("regime_labels")
        assert labels.payload[-1] == "trending_bull"

    def test_label_pipeline(self):
        manager = PluginManager()
        register_label_plugins(manager)
        builder = LabelPipelineBuilder(manager)
        rows = [_kline_row(close=close, index=index) for index, close in enumerate([100.0, 105.0, 103.0, 110.0])]
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="klines", payload=rows))
        builder.run(ctx, ["direction_label", "regime_label"])
        assert "direction_labels" in ctx.keys()
        assert "regime_labels" in ctx.keys()

    def test_feature_then_label_pipeline(self):
        manager = PluginManager()
        register_feature_plugins(manager)
        register_label_plugins(manager)
        feature_builder = FeaturePipelineBuilder(manager)
        label_builder = LabelPipelineBuilder(manager)
        rows = [_kline_row(close=close, index=index) for index, close in enumerate([100.0, 105.0, 103.0, 110.0])]
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="klines", payload=rows))
        feature_builder.run(ctx, ["ohlc_feature"])
        labeler = manager.get("platform.labels", "direction_label", config={"horizon": 1, "threshold_pct": 0.01})
        labeler.generate(ctx)
        assert ctx.require("direction_labels").payload[0] == "bullish"
