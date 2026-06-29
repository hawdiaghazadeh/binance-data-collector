"""ClickHouse schema definitions and initialization."""

from __future__ import annotations

KLINES_COLUMNS = [
    "symbol",
    "timeframe",
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "quote_volume",
    "trade_count",
    "taker_buy_volume",
    "taker_buy_quote_volume",
]

CREATE_DATABASE_SQL = """
CREATE DATABASE IF NOT EXISTS {database}
"""

CREATE_KLINES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS {database}.{table} (
    symbol LowCardinality(String),
    timeframe LowCardinality(String),
    open_time DateTime64(3, 'UTC'),
    open Float64,
    high Float64,
    low Float64,
    close Float64,
    volume Float64,
    close_time DateTime64(3, 'UTC'),
    quote_volume Float64,
    trade_count UInt32,
    taker_buy_volume Float64,
    taker_buy_quote_volume Float64,
    INDEX idx_symbol symbol TYPE bloom_filter GRANULARITY 4,
    INDEX idx_timeframe timeframe TYPE bloom_filter GRANULARITY 4
) ENGINE = ReplacingMergeTree()
PARTITION BY toYYYYMM(open_time)
ORDER BY (symbol, timeframe, open_time)
SETTINGS index_granularity = 8192
"""

CREATE_IMPORT_STATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS {database}.{import_state_table} (
    file_path String,
    symbol LowCardinality(String),
    timeframe LowCardinality(String),
    year UInt16,
    month UInt8,
    rows_inserted UInt64,
    imported_at DateTime64(3, 'UTC') DEFAULT now64(3)
) ENGINE = ReplacingMergeTree(imported_at)
ORDER BY file_path
SETTINGS index_granularity = 8192
"""


def ensure_schema(
    client,
    database: str,
    table: str,
    import_state_table: str,
) -> None:
    """Create database and tables if they do not exist."""
    client.command(CREATE_DATABASE_SQL.format(database=database))
    client.command(
        CREATE_KLINES_TABLE_SQL.format(database=database, table=table)
    )
    client.command(
        CREATE_IMPORT_STATE_TABLE_SQL.format(
            database=database,
            import_state_table=import_state_table,
        )
    )
