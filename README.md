# Crypto Historical Data Pipeline

Production-grade pipeline for downloading Binance USDT-M futures kline data from [Binance Vision](https://data.binance.vision) and importing it into ClickHouse.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Downloader │────▶│  ZIP files   │────▶│  Importer   │
│  (async)    │     │  /downloads  │     │  (threads)  │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                 │
                                          ┌──────▼──────┐
                                          │ ClickHouse  │
                                          │   klines    │
                                          └──────┬──────┘
                                                 │
                                          ┌──────▼──────┐
                                          │   Grafana   │
                                          │  dashboards │
                                          └─────────────┘
```

| Service     | Responsibility                          |
|-------------|-----------------------------------------|
| `downloader`| Download monthly ZIP files from Binance   |
| `importer`  | Parse ZIPs in memory, batch insert to DB|
| `clickhouse`| Time-series storage with partitioning     |
| `grafana`   | Charts, data overview, quality monitoring |

The platform supports a plugin-driven architecture for extensibility (features, strategies, RL, trading). See [docs/PLATFORM_ARCHITECTURE.md](docs/PLATFORM_ARCHITECTURE.md) and [docs/PLUGINS.md](docs/PLUGINS.md).

## Project Structure

```
├── config/
│   └── config.yaml          # All runtime configuration
├── docker/
│   ├── clickhouse/init/     # Schema initialization SQL
│   ├── grafana/             # Grafana provisioning & dashboards
│   ├── downloader/Dockerfile
│   └── importer/Dockerfile
├── services/
│   ├── shared/              # Config, logging, validation, models
│   ├── downloader/          # Async download service
│   ├── importer/            # Concurrent import service
│   └── database/            # ClickHouse client and schema
├── quant_platform/          # Plugin registry & extensible platform core
├── docs/                    # Architecture, migration, plugin guides
├── scripts/                 # Utility scripts
├── tests/                   # Unit tests
├── downloads/               # Downloaded ZIP files (volume)
├── logs/                    # Structured logs (volume)
├── docker-compose.yml
└── pyproject.toml
```

## Requirements

- Docker & Docker Compose
- Python 3.13+ (for local development)

## Quick Start (Docker)

```bash
# 1. Clone and enter project
cd crypto-pipeline

# 2. Copy environment file (optional)
cp .env.example .env

# 3. Start ClickHouse
docker compose up -d clickhouse

# 4. Start Grafana (optional — for charts and data monitoring)
docker compose up -d grafana

# 5. Run downloader
docker compose --profile download up downloader

# 6. Run importer
docker compose --profile import up importer

# 7. Run full pipeline (downloader first, then importer)
docker compose --profile pipeline up
```

The `pipeline` profile runs services in order: **ClickHouse → Downloader → Importer**. The importer waits until the downloader exits successfully before starting.

```bash
# Import only (skip downloader — use when ZIPs already exist)
docker compose --profile import up importer
```

## Grafana

Grafana connects to ClickHouse automatically and loads pre-built dashboards in the **Crypto** folder.

```bash
# Start ClickHouse + Grafana
docker compose up -d clickhouse grafana
```

Open [http://localhost:3080](http://localhost:3080) (default login: `admin` / `admin`).

| Dashboard            | Purpose                                              |
|----------------------|------------------------------------------------------|
| Crypto Data Overview | Row counts, coverage per symbol/timeframe, imports   |
| Crypto Price Charts  | OHLC, volume, quote volume — filter by symbol & TF    |
| Crypto Data Quality  | Duplicates, invalid OHLC, import history             |

Override credentials via `.env`:

```bash
GRAFANA_PORT=3080
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=your-secure-password
```

Dashboards and datasource config live in `docker/grafana/`. Edit JSON files there and restart Grafana to apply changes.

## Local Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest -v

# Run downloader locally
CONFIG_PATH=config/config.yaml python -m services.downloader.main

# Run importer locally (ClickHouse must be running)
CONFIG_PATH=config/config.yaml python -m services.importer.main
```

For local runs, update `config/config.yaml`:

```yaml
paths:
  download_dir: "./downloads"
  logs_dir: "./logs"
  state_dir: "./downloads/.state"

database:
  host: "localhost"
```

## Configuration

All settings live in `config/config.yaml`. Nothing is hardcoded.

### Symbols

```yaml
symbols:
  - BTCUSDT
  - ETHUSDT
  # Add any Binance USDT-M futures symbol
```

### Timeframes

```yaml
timeframes:
  - 1m
  - 5m
  - 1h
  - 1d
  # All Binance monthly timeframes supported
```

### Downloader

| Key                    | Default | Description                    |
|------------------------|---------|--------------------------------|
| `max_concurrent`       | 8       | Parallel download connections  |
| `retry_count`          | 5       | Retries per failed download    |
| `request_timeout_seconds` | 120  | HTTP timeout                   |
| `verify_checksum`      | true    | SHA256 verification            |
| `chunk_size_bytes`     | 1048576 | Stream chunk size              |

### Importer

| Key                  | Default | Description                     |
|----------------------|---------|---------------------------------|
| `max_workers`        | 4       | Parallel import threads         |
| `batch_size`         | 50000   | Rows per ClickHouse insert      |
| `retry_count`        | 3       | Retries per failed import       |
| `delete_after_import`| false   | Remove ZIP after successful import |
| `validate_gaps`      | true    | Detect missing candles          |

### Environment Overrides

```bash
export SYMBOLS=BTCUSDT,ETHUSDT
export DATABASE__HOST=clickhouse
export DOWNLOADER__MAX_CONCURRENT=16
```

## Database Schema

**Database:** `crypto`

**Table:** `klines`

| Column                  | Type              | Description          |
|-------------------------|-------------------|----------------------|
| `symbol`                | LowCardinality(String) | Trading pair    |
| `timeframe`             | LowCardinality(String) | Candle interval   |
| `open_time`             | DateTime64(3, UTC)| Candle open          |
| `open`                  | Float64           | Open price           |
| `high`                  | Float64           | High price           |
| `low`                   | Float64           | Low price            |
| `close`                 | Float64           | Close price          |
| `volume`                | Float64           | Base asset volume    |
| `close_time`            | DateTime64(3, UTC)| Candle close         |
| `quote_volume`          | Float64           | Quote asset volume   |
| `trade_count`           | UInt32            | Number of trades     |
| `taker_buy_volume`      | Float64           | Taker buy base vol   |
| `taker_buy_quote_volume`| Float64           | Taker buy quote vol  |

- **Engine:** `ReplacingMergeTree` (deduplication on merge)
- **Partition:** `toYYYYMM(open_time)`
- **Order By:** `(symbol, timeframe, open_time)`
- **Indexes:** Bloom filters on `symbol` and `timeframe`

### Example Queries

```sql
-- Latest BTC 1h candles
SELECT *
FROM crypto.klines
WHERE symbol = 'BTCUSDT' AND timeframe = '1h'
ORDER BY open_time DESC
LIMIT 100;

-- Row counts per symbol
SELECT symbol, timeframe, count() AS rows
FROM crypto.klines
GROUP BY symbol, timeframe
ORDER BY symbol, timeframe;

-- Date range coverage
SELECT symbol, timeframe,
       min(open_time) AS first_candle,
       max(open_time) AS last_candle,
       count() AS total
FROM crypto.klines
WHERE symbol = 'ETHUSDT'
GROUP BY symbol, timeframe;
```

## Adding Symbols

Edit `config/config.yaml`:

```yaml
symbols:
  - BTCUSDT
  - ETHUSDT
  - NEWCOINUSDT   # Just add here
```

Restart the downloader and importer. No code changes required.

## Adding Timeframes

```yaml
timeframes:
  - 1m
  - 4h
  - 1w
```

## Data Validation

The importer validates every row:

- Duplicate `open_time` detection
- OHLC range validation (high ≥ low, open/close within range)
- Empty file detection
- Corrupted ZIP detection
- Missing candle gap warnings
- Timestamp sanity checks

All issues are logged to `logs/errors.log` and `logs/importer.log`.

## Data Integrity (Import)

Each monthly ZIP file is imported **transactionally**:

| Step | Action |
|------|--------|
| 1 | Delete existing rows for that symbol/timeframe/month |
| 2 | Stream-insert all candles from the ZIP |
| 3 | Strict validation (no invalid/duplicate rows in CSV) |
| 4 | Mark file complete in `import_state` only on full success |
| On failure | Roll back — delete month's rows, do not mark file |

Files are processed **in chronological order** (`serial_import: true` by default):
`symbol → timeframe → year → month` (oldest first).

Re-running the importer skips files already in `import_state`. Failed files are retried from scratch with a clean month.

Config (`config/config.yaml`):

```yaml
importer:
  serial_import: true        # chronological, one file at a time
  strict_validation: true    # fail file on any invalid/duplicate row
  rollback_on_failure: true  # delete partial data on error
```

## Resumability

| Feature              | Mechanism                                      |
|----------------------|------------------------------------------------|
| Download resume      | Skip existing valid ZIP files on disk          |
| Import resume        | `import_state` table tracks completed files    |
| Failed import        | Month rolled back; file retried on next run    |
| Checksum verification| SHA256 from Binance `.CHECKSUM` files          |
| Graceful shutdown    | SIGINT/SIGTERM handled in both services        |

## Logging

Structured logs written to:

| File               | Content                    |
|--------------------|----------------------------|
| `logs/downloader.log` | Download progress       |
| `logs/importer.log`   | Import progress          |
| `logs/errors.log`     | All ERROR level events   |
| `logs/statistics.log` | Run summaries            |

Set `logging.json_logs: true` in config for JSON output.

## Troubleshooting

### ClickHouse not reachable

```bash
docker compose ps
docker compose logs clickhouse
curl http://localhost:8123/ping
```

### Download failures

- Check network connectivity to `data.binance.vision`
- Increase `downloader.retry_count` and `request_timeout_seconds`
- Review `logs/downloader.log` and `logs/errors.log`

### Import failures

- Verify ZIP integrity: files must not be corrupted
- Ensure ClickHouse has sufficient disk space
- Reduce `importer.batch_size` if memory is limited
- Check `logs/importer.log` for validation errors

### Duplicate data

The importer prevents duplicates at import time (delete-before-insert per month). For verification:

```sql
SELECT symbol, timeframe, open_time, count() AS cnt
FROM crypto.klines
GROUP BY symbol, timeframe, open_time
HAVING cnt > 1
LIMIT 20;
```

Should return zero rows after successful imports.

### Reset import state

```sql
TRUNCATE TABLE crypto.import_state;
```

Then re-run the importer.

## Scaling to All Symbols

To download all Binance USDT-M futures symbols, replace the `symbols` list in config with your full symbol list. The architecture supports any number of symbols and timeframes without code changes.

Recommended production settings for large-scale downloads:

```yaml
downloader:
  max_concurrent: 16
  retry_count: 5

importer:
  max_workers: 8
  batch_size: 100000
```

## License

MIT
