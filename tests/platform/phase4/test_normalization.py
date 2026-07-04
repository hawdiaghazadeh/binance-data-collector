"""Phase 4 normalization registry tests."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.manager import PluginManager
from quant_platform.features.pipeline import FeaturePipelineBuilder, register_feature_plugins
from quant_platform.normalizations.pipeline import NormalizationPipelineBuilder, register_normalization_plugins
from quant_platform.normalizations.symbol import normalize_symbol, normalize_timeframe, normalize_kline_rows
from quant_platform.normalizations.z_score import compute_z_score, extract_numeric_series
from services.shared.models import KlineRow


def _sample_klines(*, symbol: str = "btc-usdt", timeframe: str = "60m") -> list[KlineRow]:
    t0 = datetime(2024, 1, 1, tzinfo=timezone.utc)
    t1 = datetime(2024, 1, 1, 1, tzinfo=timezone.utc)
    return [
        KlineRow(
            symbol=symbol,
            timeframe=timeframe,
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
    closes = [100.0, 110.0, 90.0, 120.0, 105.0]
    for index, close in enumerate(closes):
        open_time = base.replace(hour=index)
        close_time = base.replace(hour=index + 1)
        rows.append(
            KlineRow(
                symbol="eth/usdt",
                timeframe="1hour",
                open_time=open_time,
                open=close - 5,
                high=close + 5,
                low=close - 10,
                close=close,
                volume=1000.0 + index,
                close_time=close_time,
                quote_volume=close * 1000,
                trade_count=10,
                taker_buy_volume=500.0,
                taker_buy_quote_volume=25000.0,
            )
        )
    return rows


class TestSymbolHelpers:
    def test_normalize_symbol(self):
        assert normalize_symbol(" btc-usdt ") == "BTCUSDT"
        assert normalize_symbol("eth/usdt") == "ETHUSDT"

    def test_normalize_timeframe(self):
        assert normalize_timeframe("60m") == "1h"
        assert normalize_timeframe("1hour") == "1h"
        assert normalize_timeframe("1d") == "1d"

    def test_normalize_timeframe_invalid(self):
        with pytest.raises(ValueError, match="Unsupported timeframe"):
            normalize_timeframe("2y")


class TestZScoreHelpers:
    def test_compute_z_score_population(self):
        values = [10.0, 20.0, 30.0]
        result = compute_z_score(values, window=None)
        assert result[0] == pytest.approx(-1.0)
        assert result[1] == pytest.approx(0.0)
        assert result[2] == pytest.approx(1.0)

    def test_compute_z_score_rolling(self):
        values = [10.0, 20.0, 30.0, 40.0]
        result = compute_z_score(values, window=2)
        assert result[0] is None
        assert result[1] == pytest.approx(1.0)
        assert result[2] == pytest.approx(1.0)
        assert result[3] == pytest.approx(1.0)

    def test_extract_numeric_series(self):
        rows = _sample_klines()
        assert extract_numeric_series(rows, "close") == [105.0]


class TestNormalizationRegistry:
    def test_symbol_normalizer(self):
        manager = PluginManager()
        register_normalization_plugins(manager)
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="klines", payload=_sample_klines()))
        normalizer = manager.get("platform.normalizations", "symbol_normalizer")
        normalizer.normalize(ctx)
        klines = ctx.require("klines")
        row = klines.payload[0]
        assert row.symbol == "BTCUSDT"
        assert row.timeframe == "1h"
        assert klines.metadata["normalized"] is True

    def test_z_score_normalizer(self):
        manager = PluginManager()
        register_normalization_plugins(manager)
        rows = _multi_klines()
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="klines", payload=rows))
        normalizer = manager.get("platform.normalizations", "z_score", config={"field": "close", "window": 3})
        normalizer.normalize(ctx)
        z_scores = ctx.require("z_score")
        assert len(z_scores.payload) == len(rows)
        assert z_scores.payload[0] is None
        assert z_scores.payload[1] is None
        assert z_scores.payload[2] is not None

    def test_normalization_pipeline(self):
        manager = PluginManager()
        register_normalization_plugins(manager)
        builder = NormalizationPipelineBuilder(manager)
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="klines", payload=_multi_klines()))
        builder.run(ctx, ["symbol_normalizer", "z_score"])
        row = ctx.require("klines").payload[0]
        assert row.symbol == "ETHUSDT"
        assert row.timeframe == "1h"
        assert "z_score" in ctx.keys()

    def test_normalize_then_feature_pipeline(self):
        manager = PluginManager()
        register_normalization_plugins(manager)
        register_feature_plugins(manager)
        norm_builder = NormalizationPipelineBuilder(manager)
        feature_builder = FeaturePipelineBuilder(manager)
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="klines", payload=_sample_klines(symbol="btc/usdt", timeframe="60min")))
        norm_builder.run(ctx, ["symbol_normalizer"])
        feature_builder.run(ctx, ["ohlc_feature", "volume_feature"])
        row = ctx.require("klines").payload[0]
        assert row.symbol == "BTCUSDT"
        assert row.timeframe == "1h"
        assert ctx.require("ohlc").payload[0]["close"] == 105.0
        assert ctx.require("volume").payload == [1000.0]


class TestNormalizationHelpers:
    def test_normalize_kline_rows_dict(self):
        rows = [{"symbol": " btc-usdt ", "timeframe": "60m", "close": 1.0}]
        normalized = normalize_kline_rows(rows)
        assert normalized[0]["symbol"] == "BTCUSDT"
        assert normalized[0]["timeframe"] == "1h"
