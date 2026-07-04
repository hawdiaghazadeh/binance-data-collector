# Platform Architecture

ARCH_VERSION: 1.0.0  
STATUS: living document  
PLATFORM_VERSION: 1.0.0

## Governance

This document is the **current architecture map**. It is a **living document** and will receive new versions as requirements evolve (`ARCH_VERSION` semver in doc header).

**Rules:**

1. Protocol changes for a future phase **must be finalized and approved before that phase starts**.
2. **Changing a Protocol during its assigned phase is strictly forbidden.** If a flaw is discovered mid-phase, finish the phase with a minimal workaround, then amend the doc before the next phase.
3. Each version bump records: date, author, changed Protocols, rationale.
4. Implemented phases reference a **frozen Protocol version** in `docs/MIGRATION.md`.

---

## Plugin Metadata Schema

Every plugin exposes `PLUGIN_METADATA: PluginMetadata` and a factory callable.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | str | Yes | Unique plugin identifier |
| `version` | str (SemVer) | Yes | Plugin release version |
| `platform_version_compatibility` | str | Yes | Semver specifier (e.g. `>=1.0.0,<2.0.0`) |
| `author` | str | No | Author name |
| `description` | str | No | Human-readable description |
| `license` | str | No | SPDX license |
| `tags` | list[str] | No | Search/filter tags |
| `dependencies` | list[PluginDependency] | No | Other plugins + version ranges |
| `compatible_dataset_versions` | str | No | Dataset semver range |
| `compatible_feature_versions` | str | No | Feature semver range |
| `supported_markets` | list[str] | No | e.g. `crypto`, `forex` |
| `supported_timeframes` | list[str] | No | e.g. `1m`, `1h` |
| `config_schema` | dict | No | JSON Schema for plugin config |
| `input_types` | list[str] | No | Required DataEnvelope type keys |
| `output_types` | list[str] | No | Emitted DataEnvelope type keys |
| `status` | PluginStatus | No | `enabled` / `disabled` / `deprecated` |
| `lifecycle` | PluginLifecycle | No | `singleton` / `transient` / `scoped` (default: `transient`) |
| `created_at` | datetime | No | ISO timestamp |

### Instance Lifecycle

| Value | Behavior |
|-------|----------|
| `singleton` | One instance at startup; thread-safe cache |
| `transient` | New instance per `get()` |
| `scoped` | One instance per pipeline run; cleared on run end |

### PluginStatus & disable_reason

Static: `enabled`, `disabled`, `deprecated`.  
Runtime `disable_reason`: `user_config`, `incompatible_version`, `load_crash`, `dependency_unmet`, `compatibility_rejected`.

Disabled plugins are **registered** for DAG visibility but **never instantiated**.

---

## Runtime Data Flow

### DataEnvelope

Immutable container: `type_key`, `payload`, `metadata`, `timestamp`.

### PipelineContext

Per-run bag of envelopes. Plugins **emit** and **require** by type — no direct plugin-to-plugin references.

```python
class PipelineContext:
    def emit(self, envelope: DataEnvelope) -> None: ...
    def require(self, type_key: str) -> DataEnvelope: ...
    def optional(self, type_key: str) -> DataEnvelope | None: ...
```

---

## Startup vs Runtime Performance

| Phase | Operations |
|-------|------------|
| **Startup** | Discovery, DAG resolution, compatibility checks, `CompiledExecutionGraph` build |
| **Runtime** | `CompiledExecutionGraph.execute(context)` only — zero registry lookup |

Forbidden at runtime: `importlib.metadata`, registry `get()` for pipeline steps, reflection.

---

## Safe-Mode

- `plugins.safe_mode: true` (default) — load failures disable plugin, platform continues
- `plugins.fail_fast: false` — dev/CI only

---

## Discovery Mechanisms

| Mechanism | Phase |
|-----------|-------|
| Entry points | 1 |
| `@register` decorator | 1 |
| Package scan | 2A |
| Config enable list | 2A |
| DAG resolution | 2B |
| CompiledExecutionGraph | 2B |
| Dynamic import | 5+ |
| Reflection | 10+ |

Entry-point groups: `platform.{registry_plural}` (e.g. `platform.data_providers`).

---

## Composability Patterns

- `CompositeReward` — weighted sum of reward plugins
- `CompositeRisk` — chained risk checks
- `CompositeStrategy` — ensemble strategies
- `CompositeObservation` — merged observation spaces

---

## Registry Map & Protocol Contracts

### Phase 2A — Pipeline

#### DataProviderProtocol v1.0

```python
class DataProviderProtocol(Protocol):
    def discover_files(self, symbol: str, timeframe: str) -> list[Any]: ...
    def build_download_url(self, file_info: Any) -> str: ...
```

#### StorageBackendProtocol v1.0

```python
class StorageBackendProtocol(Protocol):
    def connect(self) -> None: ...
    def close(self) -> None: ...
    def ensure_schema(self) -> None: ...
    def insert_batch(self, rows: list[Any]) -> int: ...
    def ping(self) -> bool: ...
```

#### ParserProtocol v1.0

```python
class ParserProtocol(Protocol):
    def parse_csv_lines(self, lines: Iterable[str]) -> list[Any]: ...
    def validate_rows(self, rows: list[Any], timeframe: str) -> Any: ...
```

#### DatasetBuilderProtocol v1.0

```python
class DatasetBuilderProtocol(Protocol):
    def build(self, config: dict) -> Any: ...
```

### Phase 3 — Feature

#### FeatureProtocol v1.0

```python
class FeatureProtocol(Protocol):
    def compute(self, ctx: PipelineContext) -> None: ...
```

### Phase 4 — Normalization

#### NormalizationProtocol v1.0

```python
class NormalizationProtocol(Protocol):
    def normalize(self, ctx: PipelineContext) -> None: ...
```

### Phase 5 — Indicator

#### IndicatorProtocol v1.0

```python
class IndicatorProtocol(Protocol):
    def compute(self, ctx: PipelineContext) -> None: ...
```

### Phase 6 — Market Structure

#### MarketStructureProtocol v1.0

```python
class MarketStructureProtocol(Protocol):
    def analyze(self, ctx: PipelineContext) -> None: ...
```

### Phase 7 — Label

#### LabelProtocol v1.0

```python
class LabelProtocol(Protocol):
    def generate(self, ctx: PipelineContext) -> None: ...
```

### Phase 8 — Observation

#### ObservationProtocol v1.0

```python
class ObservationProtocol(Protocol):
    def build(self, ctx: PipelineContext) -> Any: ...
```

### Phase 9 — Reward

#### RewardProtocol v1.0

```python
class RewardProtocol(Protocol):
    def calculate(self, ctx: PipelineContext) -> float: ...
```

### Phase 10 — Action

#### ActionProtocol v1.0

```python
class ActionProtocol(Protocol):
    def sample(self, ctx: PipelineContext) -> Any: ...
    def apply(self, ctx: PipelineContext, action: Any) -> None: ...
```

### Phase 11 — Environment

#### EnvironmentProtocol v1.0

```python
class EnvironmentProtocol(Protocol):
    def reset(self) -> Any: ...
    def step(self, action: Any) -> tuple[Any, float, bool, dict]: ...
```

### Phase 12 — Strategy

#### StrategyProtocol v1.0

```python
class StrategyProtocol(Protocol):
    def on_bar(self, ctx: PipelineContext) -> None: ...
    def signals(self, ctx: PipelineContext) -> list[Any]: ...
```

### Phase 13 — Execution + Risk + Portfolio

#### ExecutionProtocol v1.0

```python
class ExecutionProtocol(Protocol):
    def execute_order(self, ctx: PipelineContext, order: Any) -> Any: ...
```

#### RiskProtocol v1.0

```python
class RiskProtocol(Protocol):
    def check(self, ctx: PipelineContext, order: Any) -> bool: ...
    def position_size(self, ctx: PipelineContext) -> float: ...
```

#### PortfolioProtocol v1.0

```python
class PortfolioProtocol(Protocol):
    def update(self, ctx: PipelineContext) -> None: ...
    def positions(self) -> dict[str, Any]: ...
```

### Phase 14 — Exchange + Broker

#### ExchangeProtocol v1.0

```python
class ExchangeProtocol(Protocol):
    def fetch_ticker(self, symbol: str) -> dict: ...
    def fetch_ohlcv(self, symbol: str, timeframe: str) -> list: ...
```

#### BrokerProtocol v1.0

```python
class BrokerProtocol(Protocol):
    def submit_order(self, order: Any) -> Any: ...
    def cancel_order(self, order_id: str) -> bool: ...
```

### Phase 15 — RL Core

#### ReplayBufferProtocol v1.0

```python
class ReplayBufferProtocol(Protocol):
    def add(self, transition: Any) -> None: ...
    def sample(self, batch_size: int) -> list: ...
```

#### RLAlgorithmProtocol v1.0

```python
class RLAlgorithmProtocol(Protocol):
    def train_step(self, batch: list) -> dict: ...
```

#### TrainingPipelineProtocol v1.0

```python
class TrainingPipelineProtocol(Protocol):
    def run(self, config: dict) -> Any: ...
```

### Phase 16 — Evaluation Pipeline

#### EvaluationPipelineProtocol v1.0

```python
class EvaluationPipelineProtocol(Protocol):
    def evaluate(self, model: Any, data: Any) -> dict: ...
```

### Phase 17 — Backtesting

#### BacktestingProtocol v1.0

```python
class BacktestingProtocol(Protocol):
    def run(self, strategy: Any, data: Any) -> dict: ...
```

### Phase 18 — Paper Trading

#### PaperTradingProtocol v1.0

```python
class PaperTradingProtocol(Protocol):
    def start(self) -> None: ...
    def stop(self) -> dict: ...
```

### Phase 19 — Live Trading

#### LiveTradingProtocol v1.0

```python
class LiveTradingProtocol(Protocol):
    def start(self) -> None: ...
    def stop(self) -> None: ...
```

### Phase 20 — Observability

#### VisualizationProtocol v1.0

#### NotificationProtocol v1.0

#### MonitoringProtocol v1.0

### Phase 21 — Configuration

#### ConfigurationProtocol v1.0

```python
class ConfigurationProtocol(Protocol):
    def validate(self, config: dict) -> dict: ...
```

---

## Dependency Rules (Design)

- Feature may depend on DataProvider (via PipelineContext, not direct)
- Indicator depends on Feature output envelopes
- Strategy may depend on Feature, Indicator, MarketStructure
- Execution depends on Portfolio + Risk
- RL Core: TrainingPipeline → RLAlgorithm → ReplayBuffer

---

## Marketplace Readiness (Design Only — Phase 22+)

Hooks: entry_points + pip install, PluginStatus enable/disable, semver update checks, registry deregister on remove.

---

## Phase Roadmap

See [Complete Registry Map](../README.md) and `docs/MIGRATION.md` for implementation status.
