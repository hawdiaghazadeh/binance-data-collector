"""Phase 6 market structure registry tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.manager import PluginManager
from quant_platform.features.pipeline import FeaturePipelineBuilder, register_feature_plugins
from quant_platform.market_structure.bars import Bar, to_bars
from quant_platform.market_structure.bos_choch import detect_bos_choch
from quant_platform.market_structure.fvg import detect_fvg
from quant_platform.market_structure.order_blocks import detect_order_blocks
from quant_platform.market_structure.pipeline import MarketStructurePipelineBuilder, register_market_structure_plugins
from quant_platform.market_structure.swings import find_swings
from services.shared.models import KlineRow


def _bar(
    *,
    open_: float,
    high: float,
    low: float,
    close: float,
    index: int = 0,
) -> Bar:
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


class TestMarketStructureCompute:
    def test_find_swings(self):
        bars = [
            _bar(open_=10, high=12, low=10, close=11, index=0),
            _bar(open_=11, high=12, low=8, close=9, index=1),
            _bar(open_=9, high=11, low=9, close=10, index=2),
            _bar(open_=10, high=14, low=10, close=13, index=3),
            _bar(open_=13, high=13, low=11, close=12, index=4),
        ]
        swings = find_swings(bars, lookback=1)
        kinds = {(swing.index, swing.kind) for swing in swings}
        assert (1, "low") in kinds
        assert (3, "high") in kinds

    def test_detect_bullish_fvg(self):
        bars = [
            _bar(open_=10, high=10, low=9, close=9.5, index=0),
            _bar(open_=9.5, high=11, low=9, close=10, index=1),
            _bar(open_=12, high=13, low=12, close=12.5, index=2),
        ]
        gaps = detect_fvg(bars)
        assert len(gaps) == 1
        assert gaps[0]["direction"] == "bullish"
        assert gaps[0]["bottom"] == 10
        assert gaps[0]["top"] == 12

    def test_detect_bearish_fvg(self):
        bars = [
            _bar(open_=10, high=11, low=10, close=10.5, index=0),
            _bar(open_=10.5, high=10.8, low=9, close=9.5, index=1),
            _bar(open_=9, high=9.2, low=8, close=8.5, index=2),
        ]
        gaps = detect_fvg(bars)
        assert len(gaps) == 1
        assert gaps[0]["direction"] == "bearish"

    def test_detect_order_block_bullish(self):
        bars = [
            _bar(open_=10, high=10, low=9, close=9, index=0),
            _bar(open_=9, high=9.2, low=8.9, close=9.1, index=1),
            _bar(open_=9.1, high=11, low=9, close=10.8, index=2),
        ]
        blocks = detect_order_blocks(bars, displacement_pct=0.05)
        assert len(blocks) == 1
        assert blocks[0]["direction"] == "bullish"
        assert blocks[0]["index"] == 0

    def test_detect_bos_choch(self):
        bars = [
            _bar(open_=10, high=12, low=10, close=11, index=0),
            _bar(open_=11, high=12, low=8, close=9, index=1),
            _bar(open_=9, high=11, low=9, close=10, index=2),
            _bar(open_=10, high=14, low=10, close=13, index=3),
            _bar(open_=13, high=13, low=11, close=12, index=4),
            _bar(open_=12, high=12, low=9, close=10, index=5),
            _bar(open_=10, high=11, low=8, close=9, index=6),
            _bar(open_=9, high=16, low=9, close=15, index=7),
        ]
        bos, choch = detect_bos_choch(bars, swing_lookback=1)
        assert bos or choch
        combined = bos + choch
        assert any(event["kind"].startswith("bullish") for event in combined)


class TestMarketStructureRegistry:
    def test_bos_choch_plugin(self):
        manager = PluginManager()
        register_market_structure_plugins(manager)
        rows = [
            _kline_row(open_=10, high=12, low=10, close=11, index=0),
            _kline_row(open_=11, high=12, low=8, close=9, index=1),
            _kline_row(open_=9, high=11, low=9, close=10, index=2),
            _kline_row(open_=10, high=14, low=10, close=13, index=3),
            _kline_row(open_=13, high=13, low=11, close=12, index=4),
            _kline_row(open_=12, high=12, low=9, close=10, index=5),
            _kline_row(open_=10, high=11, low=8, close=9, index=6),
            _kline_row(open_=9, high=16, low=9, close=15, index=7),
        ]
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="klines", payload=rows))
        analyzer = manager.get("platform.market_structures", "bos_choch", config={"swing_lookback": 1})
        analyzer.analyze(ctx)
        structure = ctx.require("market_structure")
        assert "bos" in structure.payload
        assert "choch" in structure.payload

    def test_fvg_plugin(self):
        manager = PluginManager()
        register_market_structure_plugins(manager)
        rows = [
            _kline_row(open_=10, high=10, low=9, close=9.5, index=0),
            _kline_row(open_=9.5, high=11, low=9, close=10, index=1),
            _kline_row(open_=12, high=13, low=12, close=12.5, index=2),
        ]
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="klines", payload=rows))
        analyzer = manager.get("platform.market_structures", "fvg")
        analyzer.analyze(ctx)
        gaps = ctx.require("fvg")
        assert len(gaps.payload) == 1

    def test_order_blocks_plugin(self):
        manager = PluginManager()
        register_market_structure_plugins(manager)
        rows = [
            _kline_row(open_=10, high=10, low=9, close=9, index=0),
            _kline_row(open_=9, high=9.2, low=8.9, close=9.1, index=1),
            _kline_row(open_=9.1, high=11, low=9, close=10.8, index=2),
        ]
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="klines", payload=rows))
        analyzer = manager.get("platform.market_structures", "order_blocks", config={"displacement_pct": 0.05})
        analyzer.analyze(ctx)
        blocks = ctx.require("order_blocks")
        assert len(blocks.payload) == 1

    def test_market_structure_pipeline(self):
        manager = PluginManager()
        register_market_structure_plugins(manager)
        builder = MarketStructurePipelineBuilder(manager)
        rows = [
            _kline_row(open_=10, high=10, low=9, close=9, index=0),
            _kline_row(open_=9, high=9.2, low=8.9, close=9.1, index=1),
            _kline_row(open_=9.1, high=11, low=9, close=10.8, index=2),
        ]
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="klines", payload=rows))
        builder.run(ctx, ["fvg", "order_blocks"])
        assert "fvg" in ctx.keys()
        assert "order_blocks" in ctx.keys()

    def test_feature_then_market_structure_pipeline(self):
        manager = PluginManager()
        register_feature_plugins(manager)
        register_market_structure_plugins(manager)
        feature_builder = FeaturePipelineBuilder(manager)
        structure_builder = MarketStructurePipelineBuilder(manager)
        rows = [
            _kline_row(open_=10, high=10, low=9, close=9.5, index=0),
            _kline_row(open_=9.5, high=11, low=9, close=10, index=1),
            _kline_row(open_=12, high=13, low=12, close=12.5, index=2),
        ]
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="klines", payload=rows))
        feature_builder.run(ctx, ["ohlc_feature"])
        structure_builder.run(ctx, ["fvg"])
        assert len(ctx.require("fvg").payload) == 1


class TestMarketStructureHelpers:
    def test_to_bars_from_dict(self):
        rows = [{"open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5}]
        bars = to_bars(rows)
        assert bars[0].close == 1.5
