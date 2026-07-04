# Migration Guide

Per-phase implementation notes, frozen Protocol versions, and rollback steps.

## Phase 0 — Architecture Design

- **Deliverable:** `docs/PLATFORM_ARCHITECTURE.md` (ARCH_VERSION 1.0.0)
- **Rollback:** Delete `docs/PLATFORM_ARCHITECTURE.md`

## Phase 1 — Core Plugin Foundation

- **Frozen APIs:** `PluginMetadata`, `BaseRegistry`, `PluginManager`, `@register`
- **Rollback:** Remove `platform/core/` and `tests/platform/phase1/`

## Phase 2A — Pipeline Migration

- **Frozen Protocols:** `DataProviderProtocol` v1.0, `StorageBackendProtocol` v1.0, `ParserProtocol` v1.0, `DatasetBuilderProtocol` v1.0
- **Changes:** `services/downloader/main.py` and `services/importer/main.py` delegate via `platform.bootstrap`
- **Rollback:** Revert `main.py` files to use `DownloadWorker` / `ClickHouseClientPool` directly; remove `platform/plugins/` pipeline adapters

## Phase 2B — Dependency Graph

- **Added:** `DependencyResolver`, `CompatibilityChecker`, `CompiledExecutionGraph`, `PipelineContext`, `InstanceManager`
- **Rollback:** Set `resolve_graph=False` in bootstrap; remove Phase 2B modules

## Phase 3 — Feature Registry

- **Frozen:** `FeatureProtocol` v1.0
- **Plugins:** `ohlc_feature`, `volume_feature`

## Phases 4–21 — Domain Registries

- Reference plugins in `platform/plugins/domain_reference.py`
- Each registry group under `platform.registries.domain`

## Phase 2A Prep (G1) — Service Testability Refactor

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

## Backward Compatibility

- `config/config.yaml` without `plugins:` section works unchanged
- Docker CMD unchanged: `python -m services.downloader.main`, `python -m services.importer.main`

## Package Name

The Python package is `quant_platform/` (not `platform/`) to avoid conflict with the standard library `platform` module. Entry-point groups retain the `platform.*` namespace.
