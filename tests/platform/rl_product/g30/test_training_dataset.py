"""G30 training dataset tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from quant_platform.core.manager import PluginManager
from quant_platform.core.registry import BaseRegistry
from quant_platform.plugins.rl import RL_PLUGINS
from quant_platform.rl_product.dataset.episode import EpisodeBuilder
from quant_platform.rl_product.dataset.loader import TrainingDatasetLoader
from quant_platform.rl_product.pipeline import register_rl_product_plugins
from quant_platform.rl_product.protocols import EpisodeCursor
from quant_platform.rl_product.registry import RL_GROUP
from services.shared.models import KlineRow


def _kline_row(*, close: float, index: int = 0) -> KlineRow:
    base = datetime(2022, 1, 1, tzinfo=timezone.utc)
    open_time = base + timedelta(hours=index)
    close_time = open_time + timedelta(hours=1) - timedelta(seconds=1)
    return KlineRow(
        symbol="BTCUSDT",
        timeframe="1h",
        open_time=open_time,
        open=close - 1.0,
        high=close + 1.0,
        low=close - 2.0,
        close=close,
        volume=100.0,
        close_time=close_time,
        quote_volume=close * 100.0,
        trade_count=10,
        taker_buy_volume=50.0,
        taker_buy_quote_volume=close * 50.0,
    )


def _series(count: int) -> list[KlineRow]:
    return [_kline_row(close=100.0 + i, index=i) for i in range(count)]


class MockStorageBackend:
    def __init__(self, bars: list[KlineRow]) -> None:
        self.bars = bars
        self.range_calls = 0

    def fetch_klines_range(self, symbol: str, timeframe: str, *, start, end) -> list[KlineRow]:
        self.range_calls += 1
        return list(self.bars)


@pytest.fixture(autouse=True)
def _clean_rl_registry():
    reg = BaseRegistry.get_instance(RL_GROUP)
    for meta in reg.list_plugins():
        reg.unregister(meta.name)
    yield


class TestTrainingDatasetLoader:
    def test_load_range_single_query(self):
        bars = _series(10)
        backend = MockStorageBackend(bars)
        loader = TrainingDatasetLoader(backend)
        start = bars[0].open_time
        end = bars[-1].open_time
        loaded = loader.load_range(
            symbol="BTCUSDT",
            timeframe="1h",
            start=start,
            end=end,
        )
        assert len(loaded) == 10
        assert loader.query_count == 1
        assert backend.range_calls == 1

    def test_load_from_config(self):
        bars = _series(20)
        backend = MockStorageBackend(bars)
        loader = TrainingDatasetLoader(backend)
        config = {
            "training": {
                "symbol": "BTCUSDT",
                "timeframe": "1h",
                "train_start": "2022-01-01",
                "train_end": "2022-01-02",
            }
        }
        loaded = loader.load_from_config(config)
        assert len(loaded) == 20
        assert loader.query_count == 1


class TestEpisodeBuilder:
    def test_build_episodes_non_overlapping(self):
        bars = _series(1000)
        episodes = EpisodeBuilder.build(
            bars,
            symbol="BTCUSDT",
            timeframe="1h",
            episode_length=500,
        )
        assert len(episodes) == 2
        assert episodes[0].split == "train"
        assert episodes[1].split == "test"
        assert len(episodes[0].bars) == 500

    def test_episode_cursor_no_lookahead(self):
        bars = _series(5)
        cursor = EpisodeCursor(bars)
        assert len(cursor.view()) == 1
        cursor.advance()
        assert len(cursor.view()) == 2
        assert cursor.view()[-1].close == bars[1].close
        assert cursor.view()[0].close == bars[0].close


class TestTrainingDatasetPlugin:
    def test_plugin_load_episodes(self):
        from quant_platform.plugins.rl.training_dataset import TrainingDatasetPlugin

        bars = _series(600)
        backend = MockStorageBackend(bars)
        plugin = TrainingDatasetPlugin(storage_backend=backend)
        config = {
            "training": {
                "symbol": "BTCUSDT",
                "timeframe": "1h",
                "train_start": "2022-01-01",
                "train_end": "2022-02-01",
                "episode_length": 500,
            },
            "dataset": {"train_ratio": 0.5, "val_ratio": 0.25},
        }
        episodes = plugin.load_episodes(config)
        assert len(episodes) >= 1
        assert plugin.loader is not None
        assert plugin.loader.query_count == 1


class TestRlProductRegistration:
    def test_register_rl_product_plugins(self):
        manager = PluginManager()
        count = register_rl_product_plugins(manager)
        assert count >= 2
        assert manager.get(RL_GROUP, "training_dataset") is not None
        assert manager.get(RL_GROUP, "episode_cache") is not None

    def test_rl_plugins_metadata(self):
        names = {meta.name for meta, _ in RL_PLUGINS}
        assert "training_dataset" in names
        assert "episode_cache" in names
        assert "smc_bos_prob" in names
        assert "feature_gate" in names
