"""Domain registry interfaces — Phases 4-21."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from quant_platform.core.context import PipelineContext


@runtime_checkable
class NormalizationProtocol(Protocol):
    def normalize(self, ctx: PipelineContext) -> None: ...


@runtime_checkable
class IndicatorProtocol(Protocol):
    def compute(self, ctx: PipelineContext) -> None: ...


@runtime_checkable
class MarketStructureProtocol(Protocol):
    def analyze(self, ctx: PipelineContext) -> None: ...


@runtime_checkable
class LabelProtocol(Protocol):
    def generate(self, ctx: PipelineContext) -> None: ...


@runtime_checkable
class ObservationProtocol(Protocol):
    def build(self, ctx: PipelineContext) -> Any: ...


@runtime_checkable
class RewardProtocol(Protocol):
    def calculate(self, ctx: PipelineContext) -> float: ...


@runtime_checkable
class ActionProtocol(Protocol):
    def sample(self, ctx: PipelineContext) -> Any: ...
    def apply(self, ctx: PipelineContext, action: Any) -> None: ...


@runtime_checkable
class EnvironmentProtocol(Protocol):
    def reset(self) -> Any: ...
    def step(self, action: Any) -> tuple[Any, float, bool, dict]: ...


@runtime_checkable
class StrategyProtocol(Protocol):
    def on_bar(self, ctx: PipelineContext) -> None: ...
    def signals(self, ctx: PipelineContext) -> list[Any]: ...


@runtime_checkable
class ExecutionProtocol(Protocol):
    def execute_order(self, ctx: PipelineContext, order: Any) -> Any: ...


@runtime_checkable
class RiskProtocol(Protocol):
    def check(self, ctx: PipelineContext, order: Any) -> bool: ...
    def position_size(self, ctx: PipelineContext) -> float: ...


@runtime_checkable
class PortfolioProtocol(Protocol):
    def update(self, ctx: PipelineContext) -> None: ...
    def positions(self) -> dict[str, Any]: ...


@runtime_checkable
class ExchangeProtocol(Protocol):
    def fetch_ticker(self, symbol: str) -> dict: ...
    def fetch_ohlcv(self, symbol: str, timeframe: str) -> list: ...


@runtime_checkable
class BrokerProtocol(Protocol):
    def submit_order(self, order: Any) -> Any: ...
    def cancel_order(self, order_id: str) -> bool: ...


@runtime_checkable
class ReplayBufferProtocol(Protocol):
    def add(self, transition: Any) -> None: ...
    def sample(self, batch_size: int) -> list: ...


@runtime_checkable
class RLAlgorithmProtocol(Protocol):
    def train_step(self, batch: list) -> dict: ...


@runtime_checkable
class TrainingPipelineProtocol(Protocol):
    def run(self, config: dict) -> Any: ...


@runtime_checkable
class EvaluationPipelineProtocol(Protocol):
    def evaluate(self, model: Any, data: Any) -> dict: ...


@runtime_checkable
class BacktestingProtocol(Protocol):
    def run(self, strategy: Any, data: Any) -> dict: ...


@runtime_checkable
class PaperTradingProtocol(Protocol):
    def start(self) -> None: ...
    def stop(self) -> dict: ...


@runtime_checkable
class LiveTradingProtocol(Protocol):
    def start(self) -> None: ...
    def stop(self) -> None: ...


@runtime_checkable
class VisualizationProtocol(Protocol):
    def render(self, ctx: PipelineContext) -> Any: ...


@runtime_checkable
class NotificationProtocol(Protocol):
    def send(self, message: str, *, channel: str = "default") -> bool: ...


@runtime_checkable
class MonitoringProtocol(Protocol):
    def record_metric(self, name: str, value: float, tags: dict | None = None) -> None: ...


@runtime_checkable
class ConfigurationProtocol(Protocol):
    def validate(self, config: dict) -> dict: ...
