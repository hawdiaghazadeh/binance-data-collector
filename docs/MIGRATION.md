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
- **Rollback:** Set `plugins.resolve_graph: false` in config; remove Phase 2B runtime wiring

## Phase 2B Runtime (G2) — Bootstrap Graph + Instance Lifecycle

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

## Phase 3 — Feature Registry

- **Frozen:** `FeatureProtocol` v1.0
- **Plugins:** `ohlc_feature`, `volume_feature`, `atr_feature`, `vwap_feature`

## Phase 3 Extension (G3) — ATR & VWAP Features

- **Added:**
  - `quant_platform/plugins/atr_feature/` — Wilder ATR with configurable period
  - `quant_platform/plugins/vwap_feature/` — cumulative VWAP from typical price
- **Changed:** `register_feature_plugins()` and `pyproject.toml` entry points
- **Tests:** extended `tests/platform/phase3/test_feature.py`
- **Rollback:** Remove `atr_feature` and `vwap_feature` plugins and entry points

## Composability Extension (G4) — Strategy & Observation

- **Added:**
  - `quant_platform/composite/strategy.py` — `CompositeStrategy` (ensemble `on_bar` + weighted signals)
  - `quant_platform/composite/observation.py` — `CompositeObservation` (merged observation payload)
- **Tests:** `tests/platform/test_composite.py`
- **Rollback:** Remove `strategy.py` and `observation.py` from `quant_platform/composite/`

## Discovery Expansion (G5) — Dynamic Import & Reflection

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

## Compatibility Matrix (G6) — Cross-Version Enforcement

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

## Entry Points (G7) — Per Registry Group

- **Added:**
  - `quant_platform/registries/groups.py` — `ALL_REGISTRY_GROUPS` manifest
  - Entry points in `pyproject.toml` for all 30 registry groups
  - Named factory exports in `domain_reference.py` for domain plugins
- **Changed:**
  - `register_all_domain_plugins()` discovers via entry points before manual fallback
  - Added `platform.dataset_builders` entry point
- **Tests:** `tests/platform/test_entry_points_g7.py`
- **Rollback:** Remove domain entry-point sections from `pyproject.toml`; revert `register_all_domain_plugins()`

## Phases 4–21 — Domain Registries

- Reference plugins in `platform/plugins/domain_reference.py`
- Each registry group under `platform.registries.domain`

## Backward Compatibility

- `config/config.yaml` without `plugins:` section works unchanged
- Docker CMD unchanged: `python -m services.downloader.main`, `python -m services.importer.main`

## Package Name

The Python package is `quant_platform/` (not `platform/`) to avoid conflict with the standard library `platform` module. Entry-point groups retain the `platform.*` namespace.
