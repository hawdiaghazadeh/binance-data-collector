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
  - Named factory exports in domain plugin packages
- **Changed:**
  - `register_all_domain_plugins()` discovers via entry points before manual fallback
  - Added `platform.dataset_builders` entry point
- **Tests:** `tests/platform/test_entry_points_g7.py`
- **Rollback:** Remove domain entry-point sections from `pyproject.toml`; revert `register_all_domain_plugins()`

## Domain Plugin Split (G8) — Package Per Registry

- **Added:**
  - `quant_platform/plugins/domain/` — 25 reference plugin packages (one per domain registry)
  - `quant_platform/plugins/domain/_helpers.py` — shared metadata helpers
  - `scripts/generate_domain_plugins.py` — generator for reference plugin scaffolds
- **Changed:**
  - `domain_reference.py` is a backward-compat shim re-exporting `quant_platform.plugins.domain`
  - Entry points now target `quant_platform.plugins.domain.<plugin>:factory`
- **Tests:** `tests/platform/test_domain_split_g8.py`
- **Rollback:** Restore monolithic `domain_reference.py`; remove `plugins/domain/` packages

## Phase 4 / G9 — Normalization Registry

- **Frozen:** `NormalizationProtocol` v1.0
- **Plugins:** `symbol_normalizer` (symbol + timeframe canonicalization), `z_score` (rolling z-score on kline field)
- **Added:**
  - `quant_platform/normalizations/` — `symbol.py`, `z_score.py`, `pipeline.py`
  - `quant_platform/plugins/domain/z_score/` — rolling z-score normalizer
  - `NormalizationPipelineBuilder` + `register_normalization_plugins()`
- **Changed:** `symbol_normalizer` upgraded from stub to production implementation
- **Tests:** `tests/platform/phase4/test_normalization.py`
- **Rollback:** Remove `quant_platform/normalizations/` and `z_score` plugin; revert `symbol_normalizer` to stub; remove Phase 4 tests

## Phase 5 / G10 — Indicator Registry

- **Frozen:** `IndicatorProtocol` v1.0
- **Plugins:** `ema_indicator`, `rsi_indicator`, `macd_indicator`
- **Added:**
  - `quant_platform/indicators/` — `compute.py`, `source.py`, `pipeline.py`
  - `ClickHouseClient.fetch_klines()` + `ClickHouseStorageBackend.fetch_klines()` for indicator data loading
  - `IndicatorPipelineBuilder` + `register_indicator_plugins()`
- **Changed:** `ema_indicator` upgraded from stub to production EMA
- **Tests:** `tests/platform/phase5/test_indicator.py`
- **Rollback:** Remove `quant_platform/indicators/` and RSI/MACD plugins; revert `fetch_klines`; remove Phase 5 tests

## Phase 6 / G11 — Market Structure Registry

- **Frozen:** `MarketStructureProtocol` v1.0
- **Plugins:** `bos_choch`, `fvg`, `order_blocks`
- **Added:**
  - `quant_platform/market_structure/` — swings, BOS/CHoCH, FVG, order blocks
  - `MarketStructurePipelineBuilder` + `register_market_structure_plugins()`
- **Changed:** `bos_choch` upgraded from stub to production swing-based detection
- **Tests:** `tests/platform/phase6/test_market_structure.py`
- **Rollback:** Remove `quant_platform/market_structure/` and FVG/order block plugins; revert `bos_choch` stub; remove Phase 6 tests

## Phase 7 / G12 — Label Registry

- **Frozen:** `LabelProtocol` v1.0
- **Plugins:** `direction_label`, `regime_label`
- **Added:**
  - `quant_platform/labels/` — direction, regime, pipeline
  - `LabelPipelineBuilder` + `register_label_plugins()`
- **Changed:** `direction_label` upgraded from stub to horizon-based future direction labels
- **Tests:** `tests/platform/phase7/test_label.py`
- **Rollback:** Remove `quant_platform/labels/` and `regime_label` plugin; revert `direction_label` stub; remove Phase 7 tests

## Phase 8 / G13 — Observation Registry

- **Frozen:** `ObservationProtocol` v1.0
- **Plugins:** `candle_observation`, `portfolio_observation`, `risk_observation`
- **Added:**
  - `quant_platform/observations/` — candle, portfolio, risk builders + pipeline
  - `ObservationPipelineBuilder` + `register_observation_plugins()`
- **Changed:** `candle_observation` upgraded from raw klines stub to normalized OHLC window
- **Tests:** `tests/platform/phase8/test_observation.py`
- **Rollback:** Remove `quant_platform/observations/` and portfolio/risk plugins; revert `candle_observation` stub; remove Phase 8 tests

## Phase 9 / G14 — Reward Registry

- **Frozen:** `RewardProtocol` v1.0
- **Plugins:** `profit_reward`, `sharpe_reward`, `drawdown_penalty`
- **Added:**
  - `quant_platform/rewards/` — profit, sharpe, drawdown + pipeline
  - `RewardPipelineBuilder` + `register_reward_plugins()`
  - Weighted composition via existing `CompositeReward`
- **Changed:** `profit_reward` upgraded from stub to step PnL reward
- **Tests:** `tests/platform/phase9/test_reward.py`
- **Rollback:** Remove `quant_platform/rewards/` and sharpe/drawdown plugins; revert `profit_reward` stub; remove Phase 9 tests

## Phase 10 / G15 — Action Registry

- **Frozen:** `ActionProtocol` v1.0
- **Plugins:** `discrete_action`, `continuous_action`, `hybrid_action`
- **Added:**
  - `quant_platform/actions/` — discrete, continuous, hybrid action spaces + pipeline
  - `ActionPipelineBuilder` + `register_action_plugins()`
- **Changed:** `discrete_action` upgraded from always-hold stub to policy/signal-driven sampling
- **Tests:** `tests/platform/phase10/test_action.py`
- **Rollback:** Remove `quant_platform/actions/` and continuous/hybrid plugins; revert `discrete_action` stub; remove Phase 10 tests

## Phase 11 / G16 — Environment Registry

- **Frozen:** `EnvironmentProtocol` v1.0
- **Plugins:** `spot_env`, `futures_env`
- **Added:**
  - `quant_platform/environments/` — spot/futures Gym-like engines + bootstrap helpers
  - `EnvironmentRegistry` + `register_environment_plugins()` + `bootstrap_environment()`
- **Changed:** `spot_env` upgraded from static stub to price-driven spot simulator
- **Tests:** `tests/platform/phase11/test_environment.py`
- **Rollback:** Remove `quant_platform/environments/` and `futures_env` plugin; revert `spot_env` stub; remove Phase 11 tests

## Phase 12 / G17 — Strategy Registry

- **Frozen:** `StrategyProtocol` v1.0
- **Plugins:** `rule_based`, `smc_ict`
- **Added:**
  - `quant_platform/strategies/` — rule engine, SMC/ICT skeleton, pipeline
  - `StrategyPipelineBuilder` + `register_strategy_plugins()`
  - Weighted composition via existing `CompositeStrategy`
- **Changed:** `rule_based` upgraded from empty stub to EMA/RSI rule signals
- **Tests:** `tests/platform/phase12/test_strategy.py`
- **Rollback:** Remove `quant_platform/strategies/` and `smc_ict` plugin; revert `rule_based` stub; remove Phase 12 tests

## Phase 13 / G18 — Execution + Risk + Portfolio

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

## Phase 14 / G19 — Exchange + Broker

- **Frozen:** `ExchangeProtocol`, `BrokerProtocol` v1.0
- **Plugins:** `binance_exchange`, `paper_broker`
- **Added:**
  - `quant_platform/exchanges/` — Binance REST client + kline parsing
  - `quant_platform/brokers/` — paper broker engine
  - `quant_platform/market_connectivity/` — `MarketConnectivityPipelineBuilder` + grouped registration
- **Changed:** `binance_exchange` and `paper_broker` upgraded from stubs to production adapters
- **Tests:** `tests/platform/phase14/test_market_connectivity.py`
- **Rollback:** Remove new packages; revert exchange/broker stubs; remove Phase 14 tests

## Phase 15 / G20 — RL Core

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

## Phase 16 / G21 — Evaluation Pipeline

- **Frozen:** `EvaluationPipelineProtocol` v1.0
- **Plugins:** `walk_forward`, `holdout_eval`
- **Added:**
  - `quant_platform/evaluation_pipelines/` — walk-forward folds, holdout split, Sharpe scoring
  - `EvaluationPipelineBuilder` + `register_evaluation_plugins()`
- **Changed:** `walk_forward` upgraded from static stub to rolling fold evaluation
- **Tests:** `tests/platform/phase16/test_evaluation.py`
- **Rollback:** Remove `quant_platform/evaluation_pipelines/` and `holdout_eval` plugin; revert `walk_forward` stub; remove Phase 16 tests

## Phase 17 / G22 — Backtesting

- **Frozen:** `BacktestingProtocol` v1.0
- **Plugins:** `event_driven`, `vectorized`
- **Added:**
  - `quant_platform/backtesting/` — event-driven bar loop + vectorized weight engine
  - `BacktestPipelineBuilder` + `register_backtesting_plugins()`
- **Changed:** `event_driven` upgraded from static stub to strategy-driven simulation
- **Tests:** `tests/platform/phase17/test_backtesting.py`
- **Rollback:** Remove `quant_platform/backtesting/` and `vectorized` plugin; revert `event_driven` stub; remove Phase 17 tests

## Phase 18 / G23 — Paper Trading

- **Frozen:** `PaperTradingProtocol` v1.0
- **Plugins:** `paper_engine`
- **Added:**
  - `quant_platform/paper_trading/` — end-to-end session (strategy → paper broker → portfolio)
  - `PaperTradingPipelineBuilder` + `register_paper_trading_plugins()`
- **Changed:** `paper_engine` upgraded from no-op stub to bar-driven paper session
- **Tests:** `tests/platform/phase18/test_paper_trading.py`
- **Rollback:** Remove `quant_platform/paper_trading/`; revert `paper_engine` stub; remove Phase 18 tests

## Phase 19 / G24 — Live Trading

- **Frozen:** `LiveTradingProtocol` v1.0
- **Plugins:** `live_engine`
- **Added:**
  - `quant_platform/live_trading/` — exchange-fed session (strategy → broker → portfolio)
  - `LiveTradingPipelineBuilder` + `register_live_trading_plugins()`
  - Reuses Binance exchange adapter from Phase 14
- **Changed:** `live_engine` upgraded from no-op stub to live session with `summary` after `stop()`
- **Tests:** `tests/platform/phase19/test_live_trading.py`
- **Rollback:** Remove `quant_platform/live_trading/`; revert `live_engine` stub; remove Phase 19 tests

## Phase 20 / G25 — Observability

- **Frozen:** `VisualizationProtocol`, `NotificationProtocol`, `MonitoringProtocol` v1.0
- **Plugins:** `equity_curve`, `slack_notifier`, `structlog_monitoring`, `prometheus_metrics`
- **Added:**
  - `quant_platform/observability/` — shared event bus, Grafana panel JSON, Slack webhook, metrics export
  - `ObservabilityPipelineBuilder` + grouped registration
- **Changed:** `equity_curve`, `slack_notifier`, `structlog_monitoring` upgraded from stubs
- **Tests:** `tests/platform/phase20/test_observability.py`
- **Rollback:** Remove `quant_platform/observability/` and `prometheus_metrics` plugin; revert three upgraded stubs; remove Phase 20 tests

## Phase 21 / G26 — Configuration

- **Frozen:** `ConfigurationProtocol` v1.0
- **Plugins:** `schema_config`
- **Added:**
  - `quant_platform/configurations/` — schema registry, YAML/JSON/TOML loader, `extends`/`inherits` deep merge
  - `ConfigurationPipelineBuilder` + `register_configuration_plugins()`
- **Changed:** `schema_config` upgraded from passthrough stub to schema-driven validation with file load and inheritance
- **Tests:** `tests/platform/phase21/test_configuration.py`
- **Rollback:** Remove `quant_platform/configurations/`; revert `schema_config` stub; remove Phase 21 tests

## Phase 22 / G27 — Marketplace CLI

- **Added:**
  - `quant_platform/marketplace/` — pip-backed install/update/remove, enable/disable with config persistence
  - `quant-plugins` CLI (`install`, `enable`, `disable`, `update`, `remove`, `list`)
  - Installed plugin state file (`.quant_platform/installed_plugins.yaml`)
- **Tests:** `tests/platform/phase22/test_marketplace_cli.py`
- **Rollback:** Remove `quant_platform/marketplace/`; remove CLI entry point; remove Phase 22 tests

## Phase 22 / G28 — Plugin Manifest

- **Added:**
  - `plugin.yaml` manifest loader (`quant_platform/marketplace/manifest.py`)
  - Manifest-driven registration + setuptools entry-point cross-check (`marketplace/discovery.py`)
  - `quant-plugins inspect` CLI command
  - Install/update paths prefer manifest registration before pip entry-point discovery
- **Tests:** `tests/platform/phase22/test_marketplace_manifest.py` + fixture `plugin.yaml`
- **Rollback:** Remove manifest modules; revert install service changes; remove manifest tests

## Phase 22 / G29 — Hot Reload

- **Added:**
  - `quant_platform/marketplace/reload.py` — sync plugin enable/disable from config, rebuild `PipelineRuntime` graph
  - `quant-plugins reload` CLI command
  - Clears cached singleton/scoped instances before re-materializing pipeline plugins
- **Tests:** `tests/platform/phase22/test_marketplace_reload.py`
- **Rollback:** Remove reload module; revert CLI reload command; remove reload tests

## Phase 23 / G30 — RL Product Dataset

- **Added:**
  - `fetch_klines_range(start, end)` on `ClickHouseClient` and `ClickHouseStorageBackend`
  - `quant_platform/rl_product/` — `dataset/` (`TrainingDatasetLoader`, `EpisodeBuilder`, `EpisodeCache`), `protocols`, `graph`, `pipeline`
  - `quant_platform/registries/rl_product.py` — `platform.rl` registry group
  - Plugins: `training_dataset`, `episode_cache` under `quant_platform/plugins/rl/`
  - `register_rl_product_plugins()` + `pyproject.toml` entry points for `platform.rl`
- **Changed:** `quant_platform/registries/groups.py` — `ALL_REGISTRY_GROUPS` includes `platform.rl`
- **Tests:** `tests/platform/rl_product/g30/` + `tests/test_database.py` (`fetch_klines_range`)
- **Rollback:** Remove `quant_platform/rl_product/` and `quant_platform/plugins/rl/`; revert CH client range method; remove `platform.rl` entry points and registry

## Phase 23 / G31 — RL Product Perception

- **Added:**
  - `quant_platform/rl_product/perception/` — SMC/RTM/ICT probabilistic hints, `PerceptionCompressor`, `FeatureGate`, `PerceptionPipeline`
  - 11 hint plugins: `smc_*_prob`(4), `rtm_*`(4), `ict_*_prob`(3)
  - `perception_compressor`, `feature_gate` plugins under `platform.rl`
- **Tests:** `tests/platform/rl_product/g31/` — bounded outputs, no lookahead, no raw levels, gate zeros
- **Rollback:** Remove `rl_product/perception/` and G31 plugins; revert pyproject entry points

## Phase 23 / G32 — RL Product Observation

- **Added:**
  - `quant_platform/rl_product/observation/` — `ObservationSchema`, `PriceActionObservationBuilder`, `ObservationVector`
  - Price block (≥70%), gated context, portfolio, reserved blocks — schema v1.0 float32
  - Plugin: `price_action_observation` under `platform.rl`
- **Tests:** `tests/platform/rl_product/g32/` — budget validator, master_gate=0 zeros context
- **Rollback:** Remove `rl_product/observation/` and G32 plugin entry point

## Phases 4–21 — Domain Registries

- Reference plugins in `platform/plugins/domain_reference.py`
- Each registry group under `platform.registries.domain`

## Backward Compatibility

- `config/config.yaml` without `plugins:` section works unchanged
- Docker CMD unchanged: `python -m services.downloader.main`, `python -m services.importer.main`

## Package Name

The Python package is `quant_platform/` (not `platform/`) to avoid conflict with the standard library `platform` module. Entry-point groups retain the `platform.*` namespace.
