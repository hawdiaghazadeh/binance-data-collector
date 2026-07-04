# Crypto Historical Data Pipeline

Production-grade pipeline for downloading Binance USDT-M futures kline data from [Binance Vision](https://data.binance.vision), importing it into ClickHouse, and training RL trading agents — all from Docker with one command.

Built on **quant_platform** (plugin registry G0–G37). Package: `crypto-pipeline` (`pyproject.toml`). **387 tests**. CLIs: **`quant-train`**, **`quant-plugins`**.

---

## Table of Contents

1. [Quick Start (Docker)](#quick-start-docker)
2. [Data Folder Layout](#data-folder-layout)
3. [Compose Profiles](#compose-profiles)
4. [Multi-Symbol Configuration](#multi-symbol-configuration)
5. [RL Training](#rl-training)
6. [Grafana](#grafana)
7. [Configuration Reference](#configuration-reference)
8. [Database Schema](#database-schema)
9. [Local Development (Optional)](#local-development-optional)
10. [Platform Architecture](#platform-architecture)
11. [Plugin Authoring Guide](#plugin-authoring-guide)
12. [Troubleshooting](#troubleshooting)
13. [Project Structure](#project-structure)
14. [Appendix: Migration Guide](#appendix-migration-guide)
15. [License](#license)

---

## Quick Start (Docker)

**Requirements:** Docker and Docker Compose only.

```bash
cp .env.example .env
docker compose up --build
```

> **فارسی:** فایل `.env.example` را به `.env` کپی کنید، سپس `docker compose up --build` را اجرا کنید.

With the default `.env.example`, `COMPOSE_PROFILES=full,grafana` starts the complete stack in order:

```
ClickHouse → Downloader → Importer → RL Train   (+ Grafana dashboards)
```

| Service | Role |
|---------|------|
| `clickhouse` | Database (always starts) |
| `downloader` | Fetch monthly kline ZIPs from Binance Vision |
| `importer` | Parse ZIPs and load into ClickHouse |
| `rl-train` | PPO smoke or ClickHouse-backed training |
| `grafana` | Pre-provisioned data dashboards |

All services share one image (`crypto-platform:latest`, built from `docker/platform/Dockerfile`) and one entrypoint (`docker/platform/entrypoint.sh`).

### Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Downloader │────▶│  ZIP files   │────▶│  Importer   │
│  (async)    │     │  ./downloads │     │  (threads)  │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                 │
                                          ┌──────▼──────┐
                                          │ ClickHouse  │
                                          │   klines    │
                                          └──────┬──────┘
                    ┌────────────────────────────┼────────────────────────────┐
                    │                            │                            │
             ┌──────▼──────┐              ┌───────▼────────┐         ┌───────▼────────┐
             │   Grafana   │              │   rl-train     │         │ policy_strategy│
             │  dashboards │              │  (quant-train) │         │ → backtest     │
             └─────────────┘              └────────────────┘         └────────────────┘
```

---

## Data Folder Layout

Persistent data lives **outside** the containers on the host:

```
./
├── data/                          # All durable state (Docker volumes)
│   ├── clickhouse/                # ClickHouse data files
│   ├── clickhouse-logs/           # ClickHouse server logs
│   ├── grafana/                   # Grafana dashboards & settings
│   └── checkpoints/               # RL model checkpoints (rl-train)
├── downloads/                     # Downloaded monthly ZIP files
│   └── .state/                    # Downloader resume state
└── logs/                          # Pipeline structured logs
    ├── downloader.log
    ├── importer.log
    ├── errors.log
    └── statistics.log
```

| Path | Purpose |
|------|---------|
| `./data/clickhouse/` | Survives container rebuilds; holds all kline data |
| `./data/checkpoints/` | RL checkpoints written by `rl-train` (`CHECKPOINT_DIR`) |
| `./downloads/` | Raw Binance Vision ZIPs; safe to keep for re-import |
| `./logs/` | Service logs; check here first when debugging |

Nothing important is stored only inside ephemeral container layers.

---

## Compose Profiles

Set profiles in `.env` via `COMPOSE_PROFILES` (comma-separated) or pass `--profile` on the CLI.

| Profile | Services started | Use case |
|---------|------------------|----------|
| **`full`** | clickhouse → downloader → importer → rl-train | End-to-end: download, import, train |
| **`train`** | clickhouse → rl-train | RL smoke only (synthetic data, no download/import) |
| **`download`** | clickhouse → downloader | Fetch ZIPs only |
| **`import`** | clickhouse → importer | Import existing ZIPs (downloader optional) |
| **`grafana`** | grafana (+ clickhouse) | Monitoring dashboards |
| **`pipeline`** | clickhouse → downloader → importer | Data pipeline without RL (legacy alias) |

**Examples:**

```bash
# Full stack + Grafana (default .env)
COMPOSE_PROFILES=full,grafana docker compose up --build

# Download only
docker compose --profile download up downloader

# Import only (ZIPs already in ./downloads)
docker compose --profile import up importer

# RL smoke train only (no download/import)
docker compose --profile train up rl-train

# ClickHouse + Grafana for querying
docker compose --profile grafana up -d clickhouse grafana
```

Service dependencies are enforced by Compose: the importer waits for a healthy ClickHouse; `rl-train` waits for ClickHouse and (when present) a successful importer run.

---

## Multi-Symbol Configuration

Symbols are configured in **two places** — download vs. training — and are **not tied to config filenames**.

### Download symbols — `config/config.yaml`

```yaml
symbols:
  - BTCUSDT
  - ETHUSDT
  # Add any Binance USDT-M futures symbol
```

Restart downloader/importer after changes. No code changes required.

### Training symbol — `config/training/*.yaml`

Set `training.symbol` (and `timeframe`, date range) inside the YAML — **not** by renaming the file:

| File | Purpose |
|------|---------|
| `config/training/template.yaml` | Copy and customize for new experiments |
| `config/training/smoke.yaml` | Synthetic data; fast smoke test (`dataset.synthetic: true`) |
| `config/training/clickhouse.yaml` | Real klines from ClickHouse (`dataset.synthetic: false`) |

```yaml
# config/training/clickhouse.yaml
training:
  symbol: ETHUSDT          # any symbol you imported
  timeframe: 1h
  train_start: "2022-01-01"
  train_end: "2024-06-30"
```

To train a different pair, edit `training.symbol` in your config — do not create symbol-specific filenames like `btc_clickhouse.yaml`.

---

## RL Training

The `rl-train` service runs `quant-train` via the platform entrypoint.

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TRAIN_CONFIG` | `/config/training/smoke.yaml` | Training YAML path (inside container) |
| `TRAIN_STEPS` | `128` | Override PPO timesteps for smoke runs |
| `CHECKPOINT_DIR` | `/app/data/checkpoints` | Checkpoint output (mapped to `./data/checkpoints`) |

**Smoke train (synthetic, no ClickHouse data):**

```bash
# .env
TRAIN_CONFIG=/config/training/smoke.yaml
TRAIN_STEPS=128
COMPOSE_PROFILES=train
```

**Train on imported ClickHouse data:**

```bash
# .env
TRAIN_CONFIG=/config/training/clickhouse.yaml
TRAIN_STEPS=10000
COMPOSE_PROFILES=full,grafana
```

Ensure `training.train_start` / `train_end` in `clickhouse.yaml` match your imported date range and that `training.symbol` exists in ClickHouse.

Checkpoints land in `./data/checkpoints/`. Training output is JSON on stdout.

### RL Product Layer (G30–G37)

End-to-end RL stack on frozen klines — **27 plugins** under `platform.rl`. Deploy hook: `policy_strategy` on `platform.strategies`.

| Gate | Module | Plugins / CLI |
|------|--------|---------------|
| G30 | `rl_product/dataset/` | `training_dataset`, `episode_cache` |
| G31 | `rl_product/perception/` | SMC/RTM/ICT hints, `perception_compressor`, `feature_gate` |
| G32 | `rl_product/observation/` | `price_action_observation` (≥70% price-action block) |
| G33 | `rl_product/env/` | `rl_env_spot`, `rl_env_futures`, `execution_model` |
| G34 | `rl_product/agent/` | `ppo_torch` (split-trunk PyTorch PPO) |
| G35 | `rl_product/training/` | `online_training`, **`quant-train` CLI** |
| G36 | `rl_product/evaluation/` | `walk_forward_rl_eval`, `ablation_eval` |
| G37 | `rl_product/inference/` | `policy_inference`, `model_registry`, `policy_strategy` |

---

## Grafana

Grafana connects to ClickHouse automatically and loads dashboards in the **Crypto** folder.

Open [http://localhost:3080](http://localhost:3080) (default login: `admin` / `admin`).

| Dashboard | Purpose |
|-----------|---------|
| Crypto Data Overview | Row counts, coverage per symbol/timeframe, imports |
| Crypto Price Charts | OHLC, volume, quote volume — filter by symbol & TF |
| Crypto Data Quality | Duplicates, invalid OHLC, import history |

Override via `.env`:

```bash
GRAFANA_PORT=3080
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=your-secure-password
```

Dashboard JSON lives in `docker/grafana/`. Edit and restart Grafana to apply.

---

## Configuration Reference

All runtime settings live in `config/config.yaml`. Nothing is hardcoded in source.

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

| Key | Default | Description |
|-----|---------|-------------|
| `max_concurrent` | 8 | Parallel download connections |
| `retry_count` | 5 | Retries per failed download |
| `request_timeout_seconds` | 120 | HTTP timeout |
| `verify_checksum` | true | SHA256 verification |
| `chunk_size_bytes` | 1048576 | Stream chunk size |

### Importer

| Key | Default | Description |
|-----|---------|-------------|
| `max_workers` | 4 | Parallel import threads |
| `batch_size` | 50000 | Rows per ClickHouse insert |
| `retry_count` | 3 | Retries per failed import |
| `delete_after_import` | false | Remove ZIP after successful import |
| `validate_gaps` | true | Detect missing candles |
| `serial_import` | true | Chronological, one file at a time |
| `strict_validation` | true | Fail file on invalid/duplicate rows |
| `rollback_on_failure` | true | Delete partial month on error |

### Environment overrides

```bash
export SYMBOLS=BTCUSDT,ETHUSDT
export DATABASE__HOST=clickhouse      # use localhost for local dev
export DOWNLOADER__MAX_CONCURRENT=16
```

### Resumability

| Feature | Mechanism |
|---------|-----------|
| Download resume | Skip existing valid ZIPs on disk |
| Import resume | `import_state` table tracks completed files |
| Failed import | Month rolled back; file retried on next run |
| Checksum | SHA256 from Binance `.CHECKSUM` files |
| Graceful shutdown | SIGINT/SIGTERM handled in both services |

---

## Database Schema

**Database:** `crypto`

**Table:** `klines`

| Column | Type | Description |
|--------|------|-------------|
| `symbol` | LowCardinality(String) | Trading pair |
| `timeframe` | LowCardinality(String) | Candle interval |
| `open_time` | DateTime64(3, UTC) | Candle open |
| `open` / `high` / `low` / `close` | Float64 | OHLC prices |
| `volume` | Float64 | Base asset volume |
| `close_time` | DateTime64(3, UTC) | Candle close |
| `quote_volume` | Float64 | Quote asset volume |
| `trade_count` | UInt32 | Number of trades |
| `taker_buy_volume` | Float64 | Taker buy base vol |
| `taker_buy_quote_volume` | Float64 | Taker buy quote vol |

- **Engine:** `ReplacingMergeTree` (deduplication on merge)
- **Partition:** `toYYYYMM(open_time)`
- **Order By:** `(symbol, timeframe, open_time)`

**Table:** `import_state` — tracks successfully imported ZIP files for resume.

### Example queries

```sql
-- Latest BTC 1h candles
SELECT * FROM crypto.klines
WHERE symbol = 'BTCUSDT' AND timeframe = '1h'
ORDER BY open_time DESC LIMIT 100;

-- Row counts per symbol
SELECT symbol, timeframe, count() AS rows
FROM crypto.klines
GROUP BY symbol, timeframe;

-- Duplicate check (should return zero rows)
SELECT symbol, timeframe, open_time, count() AS cnt
FROM crypto.klines
GROUP BY symbol, timeframe, open_time
HAVING cnt > 1 LIMIT 20;
```

---

## Local Development (Optional)

For plugin work, tests, or running services outside Docker:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"            # includes torch, gymnasium, pytest

pytest -q                          # 386 tests

quant-plugins list                 # list registered plugins
quant-train train --config config/training/smoke.yaml --steps 128
```

Point the database at a local ClickHouse instance:

```bash
export DATABASE__HOST=localhost
```

Or edit `config/config.yaml`:

```yaml
paths:
  download_dir: "./downloads"
  logs_dir: "./logs"
  state_dir: "./downloads/.state"

database:
  host: "localhost"
```

Run services manually:

```bash
CONFIG_PATH=config/config.yaml python -m services.downloader.main
CONFIG_PATH=config/config.yaml python -m services.importer.main
```

Local RL checkpoints default to `.quant_platform/checkpoints/` (host) vs `./data/checkpoints/` (Docker).

---

## Platform Architecture

ARCH_VERSION: **1.0.0** · PLATFORM_VERSION: **1.0.0** · STATUS: living document

### Governance

This section is the **current architecture map** — a living document versioned by `ARCH_VERSION`.

1. Protocol changes for a future phase **must be finalized before that phase starts**.
2. **Changing a Protocol during its assigned phase is forbidden.** Finish the phase with a minimal workaround, then amend before the next phase.
3. Each version bump records: date, author, changed Protocols, rationale.
4. Implemented phases reference a frozen Protocol version in the [Migration Guide appendix](#appendix-migration-guide).

### Plugin metadata

Every plugin exposes `PLUGIN_METADATA: PluginMetadata` and a `factory()` callable.

| Field | Required | Description |
|-------|----------|-------------|
| `name`, `version` | Yes | Unique id + SemVer |
| `platform_version_compatibility` | Yes | e.g. `>=1.0.0,<2.0.0` |
| `registry_group` | Yes | Entry-point group (e.g. `platform.features`) |
| `dependencies` | No | Other plugins + version ranges |
| `compatible_dataset_versions` | No | Dataset semver range |
| `input_types` / `output_types` | No | DataEnvelope type keys |
| `lifecycle` | No | `singleton` / `transient` (default) / `scoped` |
| `status` | No | `enabled` / `disabled` / `deprecated` |

**Lifecycle:** `singleton` = one cached instance; `transient` = new per `get()`; `scoped` = one per pipeline run.

Disabled plugins stay registered for DAG visibility but are never instantiated.

### PipelineContext & DataEnvelope

Plugins communicate through a per-run data bus — **no direct plugin-to-plugin calls**.

- **DataEnvelope** — immutable: `type_key`, `payload`, `metadata`, `timestamp`
- **PipelineContext** — `emit()`, `require()`, `optional()` by envelope type

### Startup vs runtime

| Phase | Work |
|-------|------|
| **Startup** | Discovery, DAG resolution, compatibility checks, `CompiledExecutionGraph` build |
| **Runtime** | `CompiledExecutionGraph.execute(context)` only — zero registry lookup |

Forbidden at runtime: `importlib.metadata`, registry `get()` for pipeline steps, reflection.

### Safe-mode

- `plugins.safe_mode: true` (default) — load failures disable plugin, platform continues
- `plugins.fail_fast: false` — dev/CI only

### Registry groups (31)

Entry-point namespace: `platform.{registry_plural}`.

**Pipeline (Phase 2A):**

- `platform.data_providers`
- `platform.storage_backends`
- `platform.parsers`
- `platform.dataset_builders`

**Features & domain (Phases 3–21):**

- `platform.features`
- `platform.normalizations`
- `platform.indicators`
- `platform.market_structures`
- `platform.labels`
- `platform.observations`
- `platform.rewards`
- `platform.actions`
- `platform.environments`
- `platform.strategies`
- `platform.executions`
- `platform.risks`
- `platform.portfolios`
- `platform.exchanges`
- `platform.brokers`
- `platform.replay_buffers`
- `platform.rl_algorithms`
- `platform.training_pipelines`
- `platform.evaluation_pipelines`
- `platform.backtesting`
- `platform.paper_trading`
- `platform.live_trading`
- `platform.visualizations`
- `platform.notifications`
- `platform.monitoring`
- `platform.configurations`

**RL product (G30–G37):**

- `platform.rl` — 27 plugins; deploy hook `policy_strategy` also on `platform.strategies`

### Composability

- `CompositeReward` — weighted sum of reward plugins
- `CompositeRisk` — chained risk checks
- `CompositeStrategy` — ensemble strategies
- `CompositeObservation` — merged observation spaces

### Package naming

Python package: `quant_platform/` (avoids stdlib `platform` conflict). Entry-point groups retain the `platform.*` namespace.

---

## Plugin Authoring Guide

### Quick start

1. Create a plugin package under `quant_platform/plugins/your_plugin/`
2. Define `PLUGIN_METADATA` and `factory()`
3. Register via entry point in `pyproject.toml` or `@register` decorator

### Example

```python
from quant_platform.core.plugin import PluginMetadata, PluginLifecycle
from quant_platform.version import PLATFORM_VERSION

PLUGIN_METADATA = PluginMetadata(
    name="my_feature",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    lifecycle=PluginLifecycle.TRANSIENT,
    registry_group="platform.features",
)

class MyFeature:
    def compute(self, ctx):
        ...

def factory(**kwargs):
    return MyFeature()
```

### Entry point

```toml
[project.entry-points."platform.features"]
my_feature = "quant_platform.plugins.my_feature:factory"
```

### Data flow

Use `PipelineContext.emit()` / `require()` — never call other plugins directly.

### Lifecycle

- `singleton` — DB connections, shared services
- `transient` — stateless transforms (default)
- `scoped` — per pipeline run state

See [Platform Architecture](#platform-architecture) for the full specification.

---

## Troubleshooting

### ClickHouse not reachable

```bash
docker compose ps
docker compose logs clickhouse
curl http://localhost:8123/ping
```

### Download failures

- Check connectivity to `data.binance.vision`
- Increase `downloader.retry_count` and `request_timeout_seconds`
- Review `logs/downloader.log` and `logs/errors.log`

### Import failures

- Verify ZIP integrity (not corrupted)
- Ensure ClickHouse has sufficient disk space (`./data/clickhouse/`)
- Reduce `importer.batch_size` if memory is limited
- Check `logs/importer.log` for validation errors

### Reset import state

```sql
TRUNCATE TABLE crypto.import_state;
```

Then re-run the importer.

### RL / quant-train

| Symptom | Fix |
|---------|-----|
| `No module named 'torch'` | `pip install -e ".[dev]"` (included in Docker image) |
| `graph schema hash mismatch` | Deploy config must match training config exactly |
| `no episodes loaded from ClickHouse` | Check `train_start`/`train_end`, `training.symbol`, importer finished |
| Slow first run | PyTorch downloads CPU wheels on first install |

---

## Project Structure

```
├── config/
│   ├── config.yaml              # Pipeline: symbols, DB, downloader/importer
│   └── training/                # RL configs (template, smoke, clickhouse)
├── data/                        # Persistent Docker volumes (gitignored)
├── docker/
│   ├── platform/                # Unified image + entrypoint.sh
│   ├── clickhouse/init/         # Schema SQL
│   └── grafana/                 # Provisioning & dashboards
├── services/                    # Downloader, importer, database client
├── quant_platform/              # Plugin registry & RL product layer
│   ├── plugins/rl/              # 27 RL product plugins (G30–G37)
│   └── rl_product/              # Dataset → perception → env → agent → deploy
├── tests/                       # 386 unit tests
├── downloads/                   # Downloaded ZIPs
├── logs/                        # Structured logs
├── docker-compose.yml
└── pyproject.toml               # quant-train, quant-plugins entry points
```

---

## Appendix: Migration Guide

Per-phase implementation notes, frozen Protocol versions, and rollback steps.

### Phase 0 — Architecture Design

- **Deliverable:** Platform Architecture section in this README (ARCH_VERSION 1.0.0)
- **Rollback:** Remove the Platform Architecture section from this README

### Phase 1 — Core Plugin Foundation

- **Frozen APIs:** `PluginMetadata`, `BaseRegistry`, `PluginManager`, `@register`
- **Rollback:** Remove `quant_platform/core/` and `tests/platform/phase1/`

### Phase 2A — Pipeline Migration

- **Frozen Protocols:** `DataProviderProtocol` v1.0, `StorageBackendProtocol` v1.0, `ParserProtocol` v1.0, `DatasetBuilderProtocol` v1.0
- **Changes:** `services/downloader/main.py` and `services/importer/main.py` delegate via `quant_platform.bootstrap`
- **Rollback:** Revert `main.py` files to use `DownloadWorker` / `ClickHouseClientPool` directly; remove pipeline adapters

### Phase 2B — Dependency Graph

- **Added:** `DependencyResolver`, `CompatibilityChecker`, `CompiledExecutionGraph`, `PipelineContext`, `InstanceManager`
- **Rollback:** Set `plugins.resolve_graph: false` in config; remove Phase 2B runtime wiring

### Phase 2B Runtime (G2) — Bootstrap Graph + Instance Lifecycle

- **Goal:** Wire `resolve_graph`, `InstanceManager`, and `CompiledExecutionGraph` into the real startup path.
- **Added:**
  - `quant_platform/runtime.py` — `PipelineRuntime`, `compile_pipeline_graph()`, `materialize_runtime()`
  - `PluginManager.get()` uses `InstanceManager` for singleton/scoped lifecycles
  - `plugins.resolve_graph` config flag (default `true`)
- **Changed:**
  - `bootstrap_pipeline()` returns `PipelineRuntime` with cached plugin handles + compiled graph
  - `services/downloader/main.py` and `services/importer/main.py` use `runtime.data_provider` / `runtime.storage_backend`
- **Tests:** `tests/platform/phase2b/test_bootstrap_runtime.py`
- **Rollback:** Set `plugins.resolve_graph: false`; revert services to `get_*` helpers; remove `runtime.py`

### Phase 2A Prep (G1) — Service Testability Refactor

- **Goal:** Extract injectable seams in `services/` without changing download/import behavior.
- **Added:**
  - `services/downloader/ports.py` — `DownloadPathResolver`, `BinanceDownloadPaths`
  - `services/importer/ports.py` — `KlineStorage`, `StoragePool`
  - `services/database/batch.py` — pure `klines_to_tuples()`
  - `services/importer/csv_parser.py` — `DefaultKlineCsvParser`, `parse_csv_bytes()`
- **Changed:**
  - `DownloadWorker` accepts optional `path_resolver`
  - `ImportWorker` accepts `storage_pool: StoragePool` (was `db_pool: ClickHouseClientPool`)
- **Tests:** `tests/test_services_seams.py`
- **Rollback:** Revert worker constructors to concrete types only; remove `ports.py` and `batch.py`

### Phase 3 — Feature Registry

- **Frozen:** `FeatureProtocol` v1.0
- **Plugins:** `ohlc_feature`, `volume_feature`, `atr_feature`, `vwap_feature`

### Phase 3 Extension (G3) — ATR & VWAP Features

- **Added:**
  - `quant_platform/plugins/atr_feature/` — Wilder ATR with configurable period
  - `quant_platform/plugins/vwap_feature/` — cumulative VWAP from typical price
- **Changed:** `register_feature_plugins()` and `pyproject.toml` entry points
- **Tests:** extended `tests/platform/phase3/test_feature.py`
- **Rollback:** Remove `atr_feature` and `vwap_feature` plugins and entry points

### Composability Extension (G4) — Strategy & Observation

- **Added:**
  - `quant_platform/composite/strategy.py` — `CompositeStrategy` (ensemble `on_bar` + weighted signals)
  - `quant_platform/composite/observation.py` — `CompositeObservation` (merged observation payload)
- **Tests:** `tests/platform/test_composite.py`
- **Rollback:** Remove `strategy.py` and `observation.py` from `quant_platform/composite/`

### Discovery Expansion (G5) — Dynamic Import & Reflection

- **Added:**
  - `discover_dynamic_import()` — explicit module path loading (`plugins.dynamic_modules`)
  - `discover_reflection_plugins()` — class-level `PLUGIN_METADATA` scan (`plugins.reflection_modules`)
  - `iter_discovery_sources()` — unified startup discovery iterator
  - `plugins.scan_packages` config (default `quant_platform.plugins`)
- **Changed:**
  - `PluginManager.discover()` uses all mechanisms and skips duplicate plugin names
  - `bootstrap_pipeline()` discovers all pipeline groups with package scan enabled
- **Tests:** `tests/platform/test_discovery_g5.py`
- **Rollback:** Remove dynamic/reflection discovery functions; clear config lists; revert bootstrap discover loop

### Compatibility Matrix (G6) — Cross-Version Enforcement

- **Added:**
  - `CompatibilityContext` — active dataset and feature versions
  - `build_compatibility_context()` — collect versions from registered plugins
  - `version_matches_spec()` helper
  - Enforcement of `compatible_dataset_versions` and `compatible_feature_versions`
- **Changed:**
  - `CompatibilityChecker` checks platform + dataset + feature matrix at startup
  - `resolve_dependency_graph()` and `batch_load()` use built context
  - `ohlc_feature` declares `compatible_dataset_versions`
- **Tests:** `tests/platform/test_compatibility_g6.py`
- **Rollback:** Revert `compatibility.py` to platform-only checks; remove matrix fields from plugins

### Entry Points (G7) — Per Registry Group

- **Added:**
  - `quant_platform/registries/groups.py` — `ALL_REGISTRY_GROUPS` manifest
  - Entry points in `pyproject.toml` for all 30 registry groups
  - Named factory exports in domain plugin packages
- **Changed:**
  - `register_all_domain_plugins()` discovers via entry points before manual fallback
  - Added `platform.dataset_builders` entry point
- **Tests:** `tests/platform/test_entry_points_g7.py`
- **Rollback:** Remove domain entry-point sections from `pyproject.toml`; revert `register_all_domain_plugins()`

### Domain Plugin Split (G8) — Package Per Registry

- **Added:**
  - `quant_platform/plugins/domain/` — 25 reference plugin packages (one per domain registry)
  - `quant_platform/plugins/domain/_helpers.py` — shared metadata helpers
  - `scripts/generate_domain_plugins.py` — generator for reference plugin scaffolds
- **Changed:**
  - `domain_reference.py` is a backward-compat shim re-exporting `quant_platform.plugins.domain`
  - Entry points now target `quant_platform.plugins.domain.<plugin>:factory`
- **Tests:** `tests/platform/test_domain_split_g8.py`
- **Rollback:** Restore monolithic `domain_reference.py`; remove `plugins/domain/` packages

### Phase 4 / G9 — Normalization Registry

- **Frozen:** `NormalizationProtocol` v1.0
- **Plugins:** `symbol_normalizer` (symbol + timeframe canonicalization), `z_score` (rolling z-score on kline field)
- **Added:**
  - `quant_platform/normalizations/` — `symbol.py`, `z_score.py`, `pipeline.py`
  - `quant_platform/plugins/domain/z_score/` — rolling z-score normalizer
  - `NormalizationPipelineBuilder` + `register_normalization_plugins()`
- **Changed:** `symbol_normalizer` upgraded from stub to production implementation
- **Tests:** `tests/platform/phase4/test_normalization.py`
- **Rollback:** Remove `quant_platform/normalizations/` and `z_score` plugin; revert `symbol_normalizer` to stub; remove Phase 4 tests

### Phase 5 / G10 — Indicator Registry

- **Frozen:** `IndicatorProtocol` v1.0
- **Plugins:** `ema_indicator`, `rsi_indicator`, `macd_indicator`
- **Added:**
  - `quant_platform/indicators/` — `compute.py`, `source.py`, `pipeline.py`
  - `ClickHouseClient.fetch_klines()` + `ClickHouseStorageBackend.fetch_klines()` for indicator data loading
  - `IndicatorPipelineBuilder` + `register_indicator_plugins()`
- **Changed:** `ema_indicator` upgraded from stub to production EMA
- **Tests:** `tests/platform/phase5/test_indicator.py`
- **Rollback:** Remove `quant_platform/indicators/` and RSI/MACD plugins; revert `fetch_klines`; remove Phase 5 tests

### Phase 6 / G11 — Market Structure Registry

- **Frozen:** `MarketStructureProtocol` v1.0
- **Plugins:** `bos_choch`, `fvg`, `order_blocks`
- **Added:**
  - `quant_platform/market_structure/` — swings, BOS/CHoCH, FVG, order blocks
  - `MarketStructurePipelineBuilder` + `register_market_structure_plugins()`
- **Changed:** `bos_choch` upgraded from stub to production swing-based detection
- **Tests:** `tests/platform/phase6/test_market_structure.py`
- **Rollback:** Remove `quant_platform/market_structure/` and FVG/order block plugins; revert `bos_choch` stub; remove Phase 6 tests

### Phase 7 / G12 — Label Registry

- **Frozen:** `LabelProtocol` v1.0
- **Plugins:** `direction_label`, `regime_label`
- **Added:**
  - `quant_platform/labels/` — direction, regime, pipeline
  - `LabelPipelineBuilder` + `register_label_plugins()`
- **Changed:** `direction_label` upgraded from stub to horizon-based future direction labels
- **Tests:** `tests/platform/phase7/test_label.py`
- **Rollback:** Remove `quant_platform/labels/` and `regime_label` plugin; revert `direction_label` stub; remove Phase 7 tests

### Phase 8 / G13 — Observation Registry

- **Frozen:** `ObservationProtocol` v1.0
- **Plugins:** `candle_observation`, `portfolio_observation`, `risk_observation`
- **Added:**
  - `quant_platform/observations/` — candle, portfolio, risk builders + pipeline
  - `ObservationPipelineBuilder` + `register_observation_plugins()`
- **Changed:** `candle_observation` upgraded from raw klines stub to normalized OHLC window
- **Tests:** `tests/platform/phase8/test_observation.py`
- **Rollback:** Remove `quant_platform/observations/` and portfolio/risk plugins; revert `candle_observation` stub; remove Phase 8 tests

### Phase 9 / G14 — Reward Registry

- **Frozen:** `RewardProtocol` v1.0
- **Plugins:** `profit_reward`, `sharpe_reward`, `drawdown_penalty`
- **Added:**
  - `quant_platform/rewards/` — profit, sharpe, drawdown + pipeline
  - `RewardPipelineBuilder` + `register_reward_plugins()`
  - Weighted composition via existing `CompositeReward`
- **Changed:** `profit_reward` upgraded from stub to step PnL reward
- **Tests:** `tests/platform/phase9/test_reward.py`
- **Rollback:** Remove `quant_platform/rewards/` and sharpe/drawdown plugins; revert `profit_reward` stub; remove Phase 9 tests

### Phase 10 / G15 — Action Registry

- **Frozen:** `ActionProtocol` v1.0
- **Plugins:** `discrete_action`, `continuous_action`, `hybrid_action`
- **Added:**
  - `quant_platform/actions/` — discrete, continuous, hybrid action spaces + pipeline
  - `ActionPipelineBuilder` + `register_action_plugins()`
- **Changed:** `discrete_action` upgraded from always-hold stub to policy/signal-driven sampling
- **Tests:** `tests/platform/phase10/test_action.py`
- **Rollback:** Remove `quant_platform/actions/` and continuous/hybrid plugins; revert `discrete_action` stub; remove Phase 10 tests

### Phase 11 / G16 — Environment Registry

- **Frozen:** `EnvironmentProtocol` v1.0
- **Plugins:** `spot_env`, `futures_env`
- **Added:**
  - `quant_platform/environments/` — spot/futures Gym-like engines + bootstrap helpers
  - `EnvironmentRegistry` + `register_environment_plugins()` + `bootstrap_environment()`
- **Changed:** `spot_env` upgraded from static stub to price-driven spot simulator
- **Tests:** `tests/platform/phase11/test_environment.py`
- **Rollback:** Remove `quant_platform/environments/` and `futures_env` plugin; revert `spot_env` stub; remove Phase 11 tests

### Phase 12 / G17 — Strategy Registry

- **Frozen:** `StrategyProtocol` v1.0
- **Plugins:** `rule_based`, `smc_ict`
- **Added:**
  - `quant_platform/strategies/` — rule engine, SMC/ICT skeleton, pipeline
  - `StrategyPipelineBuilder` + `register_strategy_plugins()`
  - Weighted composition via existing `CompositeStrategy`
- **Changed:** `rule_based` upgraded from empty stub to EMA/RSI rule signals
- **Tests:** `tests/platform/phase12/test_strategy.py`
- **Rollback:** Remove `quant_platform/strategies/` and `smc_ict` plugin; revert `rule_based` stub; remove Phase 12 tests

### Phase 13 / G18 — Execution + Risk + Portfolio

- **Frozen:** `ExecutionProtocol`, `RiskProtocol`, `PortfolioProtocol` v1.0
- **Plugins:** `simulation_execution`, `fixed_risk`, `kelly_risk`, `single_asset`, `multi_asset`
- **Added:**
  - `quant_platform/executions/` — simulated fills with slippage/fees
  - `quant_platform/risks/` — fixed fractional + Kelly criterion sizing
  - `quant_platform/portfolios/` — single- and multi-asset portfolio engines
  - `quant_platform/order_flow/` — `OrderFlowPipelineBuilder` + grouped registration
  - Weighted composition via existing `CompositeRisk`
- **Changed:** `simulation_execution`, `fixed_risk`, `single_asset` upgraded from stubs
- **Tests:** `tests/platform/phase13/test_exec_risk_portfolio.py`
- **Rollback:** Remove new packages and `kelly_risk`/`multi_asset` plugins; revert three upgraded stubs; remove Phase 13 tests

### Phase 14 / G19 — Exchange + Broker

- **Frozen:** `ExchangeProtocol`, `BrokerProtocol` v1.0
- **Plugins:** `binance_exchange`, `paper_broker`
- **Added:**
  - `quant_platform/exchanges/` — Binance REST client + kline parsing
  - `quant_platform/brokers/` — paper broker engine
  - `quant_platform/market_connectivity/` — `MarketConnectivityPipelineBuilder` + grouped registration
- **Changed:** `binance_exchange` and `paper_broker` upgraded from stubs to production adapters
- **Tests:** `tests/platform/phase14/test_market_connectivity.py`
- **Rollback:** Remove new packages; revert exchange/broker stubs; remove Phase 14 tests

### Phase 15 / G20 — RL Core

- **Frozen:** `ReplayBufferProtocol`, `RLAlgorithmProtocol`, `TrainingPipelineProtocol` v1.0
- **Plugins:** `uniform_buffer`, `ppo`, `sac`, `standard_rl_train`
- **Added:**
  - `quant_platform/replay_buffers/` — uniform random replay buffer
  - `quant_platform/rl_algorithms/` — PPO and SAC skeleton train steps
  - `quant_platform/training_pipelines/` — standard offline training loop
  - `quant_platform/rl_core/` — `RLCorePipelineBuilder` + grouped registration
- **Changed:** `uniform_buffer`, `ppo`, `standard_rl_train` upgraded from stubs
- **Tests:** `tests/platform/phase15/test_rl_core.py`
- **Rollback:** Remove new packages and `sac` plugin; revert three upgraded stubs; remove Phase 15 tests

### Phase 16 / G21 — Evaluation Pipeline

- **Frozen:** `EvaluationPipelineProtocol` v1.0
- **Plugins:** `walk_forward`, `holdout_eval`
- **Added:**
  - `quant_platform/evaluation_pipelines/` — walk-forward folds, holdout split, Sharpe scoring
  - `EvaluationPipelineBuilder` + `register_evaluation_plugins()`
- **Changed:** `walk_forward` upgraded from static stub to rolling fold evaluation
- **Tests:** `tests/platform/phase16/test_evaluation.py`
- **Rollback:** Remove `quant_platform/evaluation_pipelines/` and `holdout_eval` plugin; revert `walk_forward` stub; remove Phase 16 tests

### Phase 17 / G22 — Backtesting

- **Frozen:** `BacktestingProtocol` v1.0
- **Plugins:** `event_driven`, `vectorized`
- **Added:**
  - `quant_platform/backtesting/` — event-driven bar loop + vectorized weight engine
  - `BacktestPipelineBuilder` + `register_backtesting_plugins()`
- **Changed:** `event_driven` upgraded from static stub to strategy-driven simulation
- **Tests:** `tests/platform/phase17/test_backtesting.py`
- **Rollback:** Remove `quant_platform/backtesting/` and `vectorized` plugin; revert `event_driven` stub; remove Phase 17 tests

### Phase 18 / G23 — Paper Trading

- **Frozen:** `PaperTradingProtocol` v1.0
- **Plugins:** `paper_engine`
- **Added:**
  - `quant_platform/paper_trading/` — end-to-end session (strategy → paper broker → portfolio)
  - `PaperTradingPipelineBuilder` + `register_paper_trading_plugins()`
- **Changed:** `paper_engine` upgraded from no-op stub to bar-driven paper session
- **Tests:** `tests/platform/phase18/test_paper_trading.py`
- **Rollback:** Remove `quant_platform/paper_trading/`; revert `paper_engine` stub; remove Phase 18 tests

### Phase 19 / G24 — Live Trading

- **Frozen:** `LiveTradingProtocol` v1.0
- **Plugins:** `live_engine`
- **Added:**
  - `quant_platform/live_trading/` — exchange-fed session (strategy → broker → portfolio)
  - `LiveTradingPipelineBuilder` + `register_live_trading_plugins()`
  - Reuses Binance exchange adapter from Phase 14
- **Changed:** `live_engine` upgraded from no-op stub to live session with `summary` after `stop()`
- **Tests:** `tests/platform/phase19/test_live_trading.py`
- **Rollback:** Remove `quant_platform/live_trading/`; revert `live_engine` stub; remove Phase 19 tests

### Phase 20 / G25 — Observability

- **Frozen:** `VisualizationProtocol`, `NotificationProtocol`, `MonitoringProtocol` v1.0
- **Plugins:** `equity_curve`, `slack_notifier`, `structlog_monitoring`, `prometheus_metrics`
- **Added:**
  - `quant_platform/observability/` — shared event bus, Grafana panel JSON, Slack webhook, metrics export
  - `ObservabilityPipelineBuilder` + grouped registration
- **Changed:** `equity_curve`, `slack_notifier`, `structlog_monitoring` upgraded from stubs
- **Tests:** `tests/platform/phase20/test_observability.py`
- **Rollback:** Remove `quant_platform/observability/` and `prometheus_metrics` plugin; revert three upgraded stubs; remove Phase 20 tests

### Phase 21 / G26 — Configuration

- **Frozen:** `ConfigurationProtocol` v1.0
- **Plugins:** `schema_config`
- **Added:**
  - `quant_platform/configurations/` — schema registry, YAML/JSON/TOML loader, `extends`/`inherits` deep merge
  - `ConfigurationPipelineBuilder` + `register_configuration_plugins()`
- **Changed:** `schema_config` upgraded from passthrough stub to schema-driven validation with file load and inheritance
- **Tests:** `tests/platform/phase21/test_configuration.py`
- **Rollback:** Remove `quant_platform/configurations/`; revert `schema_config` stub; remove Phase 21 tests

### Phase 22 / G27 — Marketplace CLI

- **Added:**
  - `quant_platform/marketplace/` — pip-backed install/update/remove, enable/disable with config persistence
  - `quant-plugins` CLI (`install`, `enable`, `disable`, `update`, `remove`, `list`)
  - Installed plugin state file (`.quant_platform/installed_plugins.yaml`)
- **Tests:** `tests/platform/phase22/test_marketplace_cli.py`
- **Rollback:** Remove `quant_platform/marketplace/`; remove CLI entry point; remove Phase 22 tests

### Phase 22 / G28 — Plugin Manifest

- **Added:**
  - `plugin.yaml` manifest loader (`quant_platform/marketplace/manifest.py`)
  - Manifest-driven registration + setuptools entry-point cross-check (`marketplace/discovery.py`)
  - `quant-plugins inspect` CLI command
  - Install/update paths prefer manifest registration before pip entry-point discovery
- **Tests:** `tests/platform/phase22/test_marketplace_manifest.py` + fixture `plugin.yaml`
- **Rollback:** Remove manifest modules; revert install service changes; remove manifest tests

### Phase 22 / G29 — Hot Reload

- **Added:**
  - `quant_platform/marketplace/reload.py` — sync plugin enable/disable from config, rebuild `PipelineRuntime` graph
  - `quant-plugins reload` CLI command
  - Clears cached singleton/scoped instances before re-materializing pipeline plugins
- **Tests:** `tests/platform/phase22/test_marketplace_reload.py`
- **Rollback:** Remove reload module; revert CLI reload command; remove reload tests

### Phase 23 / G30 — RL Product Dataset

- **Added:**
  - `fetch_klines_range(start, end)` on `ClickHouseClient` and `ClickHouseStorageBackend`
  - `quant_platform/rl_product/` — `dataset/` (`TrainingDatasetLoader`, `EpisodeBuilder`, `EpisodeCache`), `protocols`, `graph`, `pipeline`
  - `quant_platform/registries/rl_product.py` — `platform.rl` registry group
  - Plugins: `training_dataset`, `episode_cache` under `quant_platform/plugins/rl/`
  - `register_rl_product_plugins()` + `pyproject.toml` entry points for `platform.rl`
- **Changed:** `quant_platform/registries/groups.py` — `ALL_REGISTRY_GROUPS` includes `platform.rl`
- **Tests:** `tests/platform/rl_product/g30/` + `tests/test_database.py` (`fetch_klines_range`)
- **Rollback:** Remove `quant_platform/rl_product/` and `quant_platform/plugins/rl/`; revert CH client range method; remove `platform.rl` entry points and registry

### Phase 23 / G31 — RL Product Perception

- **Added:**
  - `quant_platform/rl_product/perception/` — SMC/RTM/ICT probabilistic hints, `PerceptionCompressor`, `FeatureGate`, `PerceptionPipeline`
  - 11 hint plugins: `smc_*_prob`(4), `rtm_*`(4), `ict_*_prob`(3)
  - `perception_compressor`, `feature_gate` plugins under `platform.rl`
- **Tests:** `tests/platform/rl_product/g31/` — bounded outputs, no lookahead, no raw levels, gate zeros
- **Rollback:** Remove `rl_product/perception/` and G31 plugins; revert pyproject entry points

### Phase 23 / G32 — RL Product Observation

- **Added:**
  - `quant_platform/rl_product/observation/` — `ObservationSchema`, `PriceActionObservationBuilder`, `ObservationVector`
  - Price block (≥70%), gated context, portfolio, reserved blocks — schema v1.0 float32
  - Plugin: `price_action_observation` under `platform.rl`
- **Tests:** `tests/platform/rl_product/g32/` — budget validator, master_gate=0 zeros context
- **Rollback:** Remove `rl_product/observation/` and G32 plugin entry point

### Phase 23 / G33 — RL Product Environment

- **Added:**
  - `quant_platform/rl_product/env/` — `ExecutionModelProtocol`, `SimpleExecutionModel`, `PortfolioTracker`, `RewardEngine`, `RLEnvironmentBridge`, `GymnasiumRLEnv`
  - `RLProductGraph.compile()` — frozen PERCEPTION → OBSERVATION → REWARD handlers
  - Plugins: `execution_model`, `rl_env_spot`, `rl_env_futures`
- **Changed:** `RLProductGraph` expanded from schema-hash stub to full phase wiring
- **Tests:** `tests/platform/rl_product/g33/` — slippage, PnL-dominant reward, env bridge, gymnasium wrapper
- **Rollback:** Remove `rl_product/env/`; revert graph expansion; remove G33 plugins

### Phase 23 / G34 — RL Product Agent (PPO)

- **Added:**
  - `quant_platform/rl_product/agent/` — split-trunk actor-critic, GAE, PPO trainer, schema-tagged checkpoints
  - Plugin: `ppo_torch` under `platform.rl`
- **Tests:** `tests/platform/rl_product/g34/` — grad clip, checkpoint roundtrip, context trunk ablation
- **Dependencies:** `torch>=2.0.0` in dev optional extras
- **Rollback:** Remove `rl_product/agent/` and `ppo_torch` plugin

### Phase 23 / G35 — RL Product Training Loop

- **Added:**
  - `quant_platform/rl_product/training/` — `RewardNormalizer`, `EntropySchedule`, `AsyncRolloutCollector`, `OnlineTrainingLoop`
  - Optional `CurriculumScheduler` + plugin `curriculum_scheduler` (config off by default)
  - `quant-train` CLI (`quant-train train --config ...`)
  - Plugin: `online_training`
- **Tests:** `tests/platform/rl_product/g35/` — short train run, no runtime discovery, CLI smoke
- **Rollback:** Remove `rl_product/training/`; remove CLI entry point and G35 plugins

### Phase 24 / G36 — RL Product Evaluation

- **Added:**
  - `quant_platform/rl_product/evaluation/` — `PolicyEvaluator`, `WalkForwardRLEvaluator`, `AblationRunner`, `LeakageChecker`, deterministic replay
  - Plugins: `walk_forward_rl_eval`, `ablation_eval`
  - Observation `test_mode` + context-only ablation path (price block zeroed)
- **Tests:** `tests/platform/rl_product/g36/` — walk-forward folds, ablation structure, leakage checks, deterministic replay
- **Rollback:** Remove `rl_product/evaluation/` and G36 plugins

### Phase 25 / G37 — RL Product Deploy

- **Added:**
  - `quant_platform/rl_product/inference/` — `PolicyInferenceEngine`, `ModelRegistry`, `PolicyStrategy`
  - Graph schema hash parity on checkpoint load
  - Plugins: `policy_inference`, `model_registry`, `policy_strategy` (+ `platform.strategies` entry)
- **Tests:** `tests/platform/rl_product/g37/` — hash parity, strategy on_bar, backtest hook
- **Rollback:** Remove `rl_product/inference/` and G37 plugins; remove `policy_strategy` from `platform.strategies`

### Phases 4–21 — Domain Registries

- Reference plugins in `quant_platform/plugins/domain/`
- Each registry group under `quant_platform/registries/domain`

### Backward Compatibility

- `config/config.yaml` without `plugins:` section works unchanged
- Docker services use `docker/platform/entrypoint.sh` with modes `downloader`, `importer`, and `train` (replaces per-service `python -m` CMD invocations)

### Package Name

The Python package is `quant_platform/` (not `platform/`) to avoid conflict with the standard library `platform` module. Entry-point groups retain the `platform.*` namespace.

---

## License

MIT
