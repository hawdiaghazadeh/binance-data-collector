# Architecture Overview

## Design Principles

1. **Separation of concerns** — Downloader and importer are independent services with single responsibilities.
2. **Configuration-driven** — All symbols, timeframes, and runtime parameters come from YAML.
3. **Resumable** — Both services can restart without re-processing completed work.

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
7. Grafana queries ClickHouse for charts, coverage tables, and data-quality checks.

## Observability

```
docker/grafana/
├── provisioning/
│   ├── datasources/clickhouse.yaml   # Auto-configured ClickHouse connection
│   └── dashboards/default.yaml       # Dashboard file provider
└── dashboards/
    ├── crypto-overview.json
    ├── crypto-charts.json
    └── crypto-data-quality.json
```
