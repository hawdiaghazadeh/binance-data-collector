"""G30 — no per-step database query during episode rollout."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from quant_platform.rl_product.dataset.loader import TrainingDatasetLoader
from quant_platform.rl_product.protocols import EpisodeCursor
from quant_platform.plugins.rl.training_dataset import TrainingDatasetPlugin
from services.shared.models import KlineRow


def _bars(count: int) -> list[KlineRow]:
    base = datetime(2022, 1, 1, tzinfo=timezone.utc)
    rows: list[KlineRow] = []
    for i in range(count):
        open_time = base + timedelta(hours=i)
        rows.append(
            KlineRow(
                symbol="BTCUSDT",
                timeframe="1h",
                open_time=open_time,
                open=100.0,
                high=101.0,
                low=99.0,
                close=100.0 + i * 0.1,
                volume=1.0,
                close_time=open_time + timedelta(hours=1),
                quote_volume=100.0,
                trade_count=1,
                taker_buy_volume=0.5,
                taker_buy_quote_volume=50.0,
            )
        )
    return rows


class TrackingBackend:
    def __init__(self, bars: list[KlineRow]) -> None:
        self._bars = bars
        self.query_count = 0

    def fetch_klines_range(self, symbol: str, timeframe: str, *, start, end) -> list[KlineRow]:
        self.query_count += 1
        return list(self._bars)


def test_episode_rollout_zero_additional_queries():
    """Simulate env steps: load once at reset, cursor advances in RAM only."""
    backend = TrackingBackend(_bars(50))
    config = {
        "training": {
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            "train_start": "2022-01-01",
            "train_end": "2022-01-03",
            "episode_length": 20,
        }
    }
    plugin = TrainingDatasetPlugin(storage_backend=backend)
    episodes = plugin.load_episodes(config)
    assert backend.query_count == 1

    episode = episodes[0]
    cursor = EpisodeCursor(episode.bars)
    steps = 0
    while cursor.advance():
        _ = cursor.view()
        steps += 1

    assert steps == len(episode.bars) - 1
    assert backend.query_count == 1


def test_loader_rejects_missing_range_method():
    loader = TrainingDatasetLoader(object())
    with pytest.raises(RuntimeError, match="fetch_klines_range"):
        loader.load_range(
            symbol="BTCUSDT",
            timeframe="1h",
            start=datetime(2022, 1, 1, tzinfo=timezone.utc),
            end=datetime(2022, 1, 2, tzinfo=timezone.utc),
        )
