# Crypto Historical Data Pipeline

Production-grade pipeline for downloading Binance USDT-M futures kline data from [Binance Vision](https://data.binance.vision) and importing it into ClickHouse for backtesting, strategy optimization, SMC/ICT detection, scanners, signal generation, and machine learning.

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
                                          └─────────────┘
```

| Service     | Responsibility                          |
|-------------|-----------------------------------------|
| `downloader`| Download monthly ZIP files from Binance   |
| `importer`  | Parse ZIPs in memory, batch insert to DB|
| `clickhouse`| Time-series storage with partitioning     |

Future services (`scanner`, `backtester`, `api`, `websocket`) plug into the same Docker network and ClickHouse database without architectural changes.

## Project Structure

```
├── config/
│   └── config.yaml          # All runtime configuration
├── docker/
│   ├── clickhouse/init/     # Schema initialization SQL
│   ├── downloader/Dockerfile
│   └── importer/Dockerfile
├── services/
│   ├── shared/              # Config, logging, validation, models
│   ├── downloader/          # Async download service
│   ├── importer/            # Concurrent import service
│   └── database/            # ClickHouse client and schema
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

# 4. Run downloader
docker compose --profile download up downloader

# 5. Run importer
docker compose --profile import up importer

# 6. Run full pipeline (downloader first, then importer)
docker compose --profile pipeline up
```

The `pipeline` profile runs services in order: **ClickHouse → Downloader → Importer**. The importer waits until the downloader exits successfully before starting.

```bash
# Import only (skip downloader — use when ZIPs already exist)
docker compose --profile import up importer
```

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

## Resumability

| Feature              | Mechanism                                      |
|----------------------|------------------------------------------------|
| Download resume      | Skip existing valid ZIP files on disk          |
| Import resume        | `import_state` table tracks completed files    |
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

`ReplacingMergeTree` deduplicates on background merge. For immediate dedup:

```sql
OPTIMIZE TABLE crypto.klines FINAL;
```

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

## Future Extensions

The architecture supports adding these services via Docker Compose profiles:

- **scanner** — SMC/ICT, RTM pattern detection
- **backtester** — Strategy backtesting engine
- **api** — REST API for data access
- **websocket** — Real-time candle updates
- **telegram** — Alert bot

Each service reads from the same ClickHouse `crypto.klines` table.

## License

MIT
