# First-Party Plugins

Built-in plugins for the crypto-pipeline platform.

## Pipeline (Phase 2A)

| Plugin | Group | Description |
|--------|-------|-------------|
| `binance_vision` | `platform.data_providers` | Binance Vision data source |
| `clickhouse` | `platform.storage_backends` | ClickHouse storage |
| `binance_kline_csv` | `platform.parsers` | Kline CSV parser |
| `binance_klines_monthly` | `platform.dataset_builders` | Dataset pipeline composer |

## Features (Phase 3)

| Plugin | Group | Description |
|--------|-------|-------------|
| `ohlc_feature` | `platform.features` | OHLC extraction |
| `volume_feature` | `platform.features` | Volume extraction |

## Domain Reference (Phases 4–21)

See `quant_platform/plugins/domain/` for normalization, indicators, RL, trading, and observability reference plugins.
