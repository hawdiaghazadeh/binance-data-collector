"""ClickHouse client wrapper for kline data operations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Sequence

import clickhouse_connect
import structlog

from services.database.schema import KLINES_COLUMNS, ensure_schema
from services.shared.models import KlineRow

if TYPE_CHECKING:
    from services.shared.config import DatabaseConfig

logger = structlog.get_logger("database")


class ClickHouseClient:
    """
    Production ClickHouse client for batch kline inserts and import tracking.

    Uses clickhouse-connect with optional compression for high-throughput ingestion.
    """

    def __init__(self, config: DatabaseConfig) -> None:
        self._config = config
        self._client: clickhouse_connect.driver.Client | None = None

    def connect(self) -> None:
        """Establish connection and ensure schema exists."""
        self._client = clickhouse_connect.get_client(
            host=self._config.host,
            port=self._config.port,
            username=self._config.user,
            password=self._config.password or "",
            database=self._config.database,
            connect_timeout=self._config.connect_timeout,
            send_receive_timeout=self._config.send_receive_timeout,
            compress=self._config.compression,
        )
        ensure_schema(
            self._client,
            self._config.database,
            self._config.table,
            self._config.import_state_table,
        )
        logger.info(
            "database_connected",
            host=self._config.host,
            database=self._config.database,
        )

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
            logger.info("database_disconnected")

    @property
    def client(self) -> clickhouse_connect.driver.Client:
        if self._client is None:
            raise RuntimeError("Database client not connected. Call connect() first.")
        return self._client

    @property
    def full_table_name(self) -> str:
        return f"{self._config.database}.{self._config.table}"

    @property
    def import_state_table_name(self) -> str:
        return f"{self._config.database}.{self._config.import_state_table}"

    def ping(self) -> bool:
        """Health check — returns True if ClickHouse responds."""
        try:
            result = self.client.command("SELECT 1")
            return result == 1
        except Exception:
            return False

    def command(self, sql: str) -> object:
        return self.client.command(sql)

    def insert_klines(self, rows: Sequence[KlineRow]) -> int:
        """Batch insert kline rows. Returns number of rows inserted."""
        if not rows:
            return 0

        data = [row.as_tuple() for row in rows]
        self.client.insert(
            self.full_table_name,
            data,
            column_names=KLINES_COLUMNS,
        )
        logger.debug("rows_inserted", count=len(rows), table=self.full_table_name)
        return len(rows)

    def is_file_imported(self, file_path: str) -> bool:
        """Check if a ZIP file has already been imported."""
        query = f"""
            SELECT count() AS cnt
            FROM {self.import_state_table_name}
            WHERE file_path = {{path:String}}
        """
        result = self.client.query(query, parameters={"path": file_path})
        return result.first_row[0] > 0

    def mark_file_imported(
        self,
        file_path: str,
        symbol: str,
        timeframe: str,
        year: int,
        month: int,
        rows_inserted: int,
    ) -> None:
        """Record successful import in state table."""
        now = datetime.now(timezone.utc)
        self.client.insert(
            self.import_state_table_name,
            [[file_path, symbol, timeframe, year, month, rows_inserted, now]],
            column_names=[
                "file_path",
                "symbol",
                "timeframe",
                "year",
                "month",
                "rows_inserted",
                "imported_at",
            ],
        )

    def get_max_open_time(self, symbol: str, timeframe: str) -> datetime | None:
        """Return the latest open_time for a symbol/timeframe pair."""
        query = f"""
            SELECT max(open_time) AS max_time
            FROM {self.full_table_name}
            WHERE symbol = {{symbol:String}} AND timeframe = {{timeframe:String}}
        """
        result = self.client.query(
            query,
            parameters={"symbol": symbol, "timeframe": timeframe},
        )
        value = result.first_row[0]
        if value is None or str(value) == "1970-01-01 00:00:00":
            return None
        if isinstance(value, datetime):
            return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
        return None

    def count_rows(self, symbol: str | None = None, timeframe: str | None = None) -> int:
        """Count rows with optional symbol/timeframe filters."""
        conditions: list[str] = []
        params: dict[str, str] = {}

        if symbol:
            conditions.append("symbol = {symbol:String}")
            params["symbol"] = symbol
        if timeframe:
            conditions.append("timeframe = {timeframe:String}")
            params["timeframe"] = timeframe

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT count() FROM {self.full_table_name} {where}"
        result = self.client.query(query, parameters=params)
        return int(result.first_row[0])
