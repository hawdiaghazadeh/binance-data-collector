"""G30 episode cache tests."""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

from quant_platform.rl_product.dataset.cache import EpisodeCache
from quant_platform.rl_product.protocols import Episode
from services.shared.models import KlineRow


def _episode(episode_id: str) -> Episode:
    base = datetime(2022, 1, 1, tzinfo=timezone.utc)
    bars = tuple(
        KlineRow(
            symbol="BTCUSDT",
            timeframe="1h",
            open_time=base + timedelta(hours=i),
            open=100.0,
            high=101.0,
            low=99.0,
            close=100.0 + i,
            volume=1.0,
            close_time=base + timedelta(hours=i + 1),
            quote_volume=100.0,
            trade_count=1,
            taker_buy_volume=0.5,
            taker_buy_quote_volume=50.0,
        )
        for i in range(3)
    )
    return Episode(
        episode_id=episode_id,
        symbol="BTCUSDT",
        timeframe="1h",
        bars=bars,
        split="train",
        start_idx=0,
    )


class TestEpisodeCache:
    def test_lru_eviction(self):
        cache = EpisodeCache(maxsize=2, prefetch=0)
        load_count = {"n": 0}

        def loader(ep_id: str) -> Episode:
            load_count["n"] += 1
            return _episode(ep_id)

        cache.get("a", lambda: loader("a"))
        cache.get("b", lambda: loader("b"))
        cache.get("c", lambda: loader("c"))
        cache.get("a", lambda: loader("a"))

        assert load_count["n"] == 4
        assert cache.misses == 4
        assert cache.hits == 0

    def test_cache_hit(self):
        cache = EpisodeCache(maxsize=4, prefetch=0)
        load_count = {"n": 0}

        def loader() -> Episode:
            load_count["n"] += 1
            return _episode("x")

        cache.get("x", loader)
        cache.get("x", loader)
        assert load_count["n"] == 1
        assert cache.hits == 1
        assert cache.misses == 1

    def test_prefetch_populates_cache(self):
        cache = EpisodeCache(maxsize=4, prefetch=2)
        loaded: list[str] = []

        def loader(ep_id: str) -> Episode:
            loaded.append(ep_id)
            time.sleep(0.05)
            return _episode(ep_id)

        cache.prefetch(["p1", "p2"], loader)
        time.sleep(0.15)
        ep = cache.get("p1", lambda: loader("p1"))
        assert ep.episode_id == "p1"
        assert "p1" in loaded

    def test_episode_cache_plugin(self):
        from quant_platform.plugins.rl.episode_cache import EpisodeCachePlugin

        plugin = EpisodeCachePlugin(maxsize=2, prefetch=0)
        calls = {"n": 0}

        def loader() -> Episode:
            calls["n"] += 1
            return _episode("plug")

        plugin.get("plug", loader)
        plugin.get("plug", loader)
        assert calls["n"] == 1
        plugin.clear()
