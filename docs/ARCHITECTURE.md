# Architecture Overview

## Design Principles

1. **Separation of concerns** — Downloader and importer are independent services with single responsibilities.
2. **Configuration-driven** — All symbols, timeframes, and runtime parameters come from YAML.
3. **Resumable** — Both services can restart without re-processing completed work.
4. **Extensible** — New services connect to ClickHouse via the shared `database` module.

## Service Boundaries

```
services/
├── shared/       # Cross-cutting: config, logging, validation, models
├── downloader/   # HTTP → ZIP files on disk
├── importer/     # ZIP files → ClickHouse rows
└── database/     # ClickHouse schema and client
```

## Data Flow

1. Downloader discovers monthly files via Binance Vision HTML listings.
2. Files download oldest-first with concurrent async HTTP (httpx + asyncio).
3. Importer scans `/downloads/{symbol}/{timeframe}/*.zip`.
4. CSV extracted in memory (never written to disk).
5. Rows validated and batch-inserted into ClickHouse.
6. Import state recorded in `import_state` table.

## Extension Points

| Future Service | Integration Point                          |
|----------------|--------------------------------------------|
| Scanner        | Query `crypto.klines` via `ClickHouseClient` |
| Backtester     | Query `crypto.klines`, add `backtest_results` table |
| REST API       | Wrap `ClickHouseClient` in FastAPI routes  |
| WebSocket      | Subscribe to live feeds, write to ClickHouse |
