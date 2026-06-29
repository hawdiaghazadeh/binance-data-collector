-- ClickHouse initialization script
-- Executed on first container startup via docker-entrypoint-initdb.d

CREATE DATABASE IF NOT EXISTS crypto;

CREATE TABLE IF NOT EXISTS crypto.klines (
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
SETTINGS index_granularity = 8192;

CREATE TABLE IF NOT EXISTS crypto.import_state (
    file_path String,
    symbol LowCardinality(String),
    timeframe LowCardinality(String),
    year UInt16,
    month UInt8,
    rows_inserted UInt64,
    imported_at DateTime64(3, 'UTC') DEFAULT now64(3)
) ENGINE = ReplacingMergeTree(imported_at)
ORDER BY file_path
SETTINGS index_granularity = 8192;
