"""LRU episode cache with optional async prefetch."""

from __future__ import annotations

import threading
from collections import OrderedDict
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any

from quant_platform.rl_product.protocols import Episode


class EpisodeCache:
    """In-memory LRU cache; episodes loaded once and reused across rollouts."""

    __slots__ = ("_cache", "_executor", "_futures", "_lock", "_maxsize", "_prefetch", "_hits", "_misses")

    def __init__(self, *, maxsize: int = 4, prefetch: int = 2) -> None:
        if maxsize < 1:
            raise ValueError("maxsize must be >= 1")
        if prefetch < 0:
            raise ValueError("prefetch must be >= 0")
        self._maxsize = maxsize
        self._prefetch = prefetch
        self._cache: OrderedDict[str, Episode] = OrderedDict()
        self._futures: dict[str, Future[Episode]] = {}
        self._executor: ThreadPoolExecutor | None = None
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    @property
    def hits(self) -> int:
        return self._hits

    @property
    def misses(self) -> int:
        return self._misses

    def _ensure_executor(self) -> ThreadPoolExecutor:
        if self._executor is None:
            workers = max(1, self._prefetch)
            self._executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="episode-prefetch")
        return self._executor

    def _store(self, episode_id: str, episode: Episode) -> None:
        self._cache[episode_id] = episode
        self._cache.move_to_end(episode_id)
        while len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)

    def get(self, episode_id: str, loader: Callable[[], Episode]) -> Episode:
        with self._lock:
            if episode_id in self._cache:
                self._hits += 1
                self._cache.move_to_end(episode_id)
                return self._cache[episode_id]

            future = self._futures.get(episode_id)
            if future is not None:
                self._misses += 1
                pending = future
            else:
                self._misses += 1
                pending = None

        if pending is not None:
            episode = pending.result()
            with self._lock:
                self._futures.pop(episode_id, None)
                self._store(episode_id, episode)
            return episode

        episode = loader()
        with self._lock:
            self._store(episode_id, episode)
        return episode

    def prefetch(self, episode_ids: list[str], loader: Callable[[str], Episode]) -> None:
        if self._prefetch <= 0 or not episode_ids:
            return
        to_fetch = episode_ids[: self._prefetch]
        with self._lock:
            for episode_id in to_fetch:
                if episode_id in self._cache or episode_id in self._futures:
                    continue
                executor = self._ensure_executor()
                self._futures[episode_id] = executor.submit(loader, episode_id)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            for future in self._futures.values():
                future.cancel()
            self._futures.clear()
            if self._executor is not None:
                self._executor.shutdown(wait=False, cancel_futures=True)
                self._executor = None
            self._hits = 0
            self._misses = 0

    def close(self) -> None:
        with self._lock:
            self._cache.clear()
            for future in self._futures.values():
                future.cancel()
            self._futures.clear()
            if self._executor is not None:
                self._executor.shutdown(wait=True, cancel_futures=True)
                self._executor = None

    def stats(self) -> dict[str, Any]:
        with self._lock:
            return {
                "size": len(self._cache),
                "maxsize": self._maxsize,
                "hits": self._hits,
                "misses": self._misses,
                "pending_prefetch": len(self._futures),
            }
