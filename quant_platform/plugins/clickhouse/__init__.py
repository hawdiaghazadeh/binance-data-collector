"""ClickHouse storage backend plugin."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from quant_platform.core.plugin import PluginLifecycle, PluginMetadata
from services.database.client import ClickHouseClient, ClickHouseClientPool
from services.shared.models import KlineRow

if TYPE_CHECKING:
    from services.shared.config import AppConfig

PLUGIN_METADATA = PluginMetadata(
    name="clickhouse",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    author="crypto-pipeline",
    description="ClickHouse storage backend for kline data",
    lifecycle=PluginLifecycle.SINGLETON,
    registry_group="platform.storage_backends",
)


class ClickHouseStorageBackend:
    def __init__(self, config: AppConfig | None = None) -> None:
        if config is None:
            from services.shared.config import load_config

            config = load_config()
        self._config = config
        self._client: ClickHouseClient | None = None

    def connect(self) -> None:
        self._client = ClickHouseClient(self._config.database)
        self._client.connect()

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None

    def ensure_schema(self) -> None:
        if self._client is None:
            self.connect()
        else:
            self._client.connect(ensure_schema_exists=True)

    def insert_batch(self, rows: list[Any]) -> int:
        if self._client is None:
            raise RuntimeError("Not connected")
        klines = [r if isinstance(r, KlineRow) else r for r in rows]
        return self._client.insert_klines(klines)

    def ping(self) -> bool:
        if self._client is None:
            self._client = ClickHouseClient(self._config.database)
            try:
                self._client.connect()
                return self._client.ping()
            finally:
                self._client.close()
                self._client = None
        return self._client.ping()

    def create_pool(self) -> ClickHouseClientPool:
        return ClickHouseClientPool(self._config.database)

    def fetch_klines(
        self,
        symbol: str,
        timeframe: str,
        *,
        limit: int = 500,
    ) -> list[KlineRow]:
        if self._client is None:
            self.connect()
        assert self._client is not None
        return self._client.fetch_klines(symbol, timeframe, limit=limit)

    def fetch_klines_range(
        self,
        symbol: str,
        timeframe: str,
        *,
        start: datetime,
        end: datetime,
    ) -> list[KlineRow]:
        if self._client is None:
            self.connect()
        assert self._client is not None
        return self._client.fetch_klines_range(symbol, timeframe, start=start, end=end)


def factory(*, config: Any = None) -> ClickHouseStorageBackend:
    return ClickHouseStorageBackend(config=config)
