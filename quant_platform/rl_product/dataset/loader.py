"""ClickHouse-backed training dataset loader — single range query per load."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from services.shared.models import KlineRow


def _parse_datetime(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        text = value.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class TrainingDatasetLoader:
    """Loads OHLCV once via storage backend fetch_klines_range (no per-step DB)."""

    __slots__ = ("_backend", "query_count")

    def __init__(self, storage_backend: Any) -> None:
        self._backend = storage_backend
        self.query_count = 0

    def load_range(
        self,
        *,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> list[KlineRow]:
        fetch_range = getattr(self._backend, "fetch_klines_range", None)
        if fetch_range is None:
            raise RuntimeError("storage backend does not support fetch_klines_range")
        self.query_count += 1
        return list(fetch_range(symbol, timeframe, start=start, end=end))

    def load_from_config(self, config: dict) -> list[KlineRow]:
        training = config.get("training", config)
        symbol = str(training["symbol"])
        timeframe = str(training["timeframe"])
        start = _parse_datetime(training["train_start"])
        end = _parse_datetime(training["train_end"])
        return self.load_range(symbol=symbol, timeframe=timeframe, start=start, end=end)
