"""Reference domain plugins for Phases 4-21."""

from __future__ import annotations

from typing import Any, Callable

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.manager import PluginManager
from quant_platform.core.plugin import PluginMetadata
from quant_platform.registries.domain import GROUP_REGISTRY_MAP

DEFAULT_PLATFORM_COMPAT = ">=1.0.0,<2.0.0"


def _meta(name: str, group: str, description: str = "") -> PluginMetadata:
    return PluginMetadata(
        name=name,
        version="1.0.0",
        platform_version_compatibility=DEFAULT_PLATFORM_COMPAT,
        description=description or f"Reference {name} plugin",
        registry_group=group,
    )


class SymbolNormalizer:
    def normalize(self, ctx: PipelineContext) -> None:
        for key in list(ctx.keys()):
            env = ctx.require(key)
            if isinstance(env.payload, list) and env.payload and isinstance(env.payload[0], dict):
                normalized = [{**row, "symbol": str(row.get("symbol", "")).upper()} for row in env.payload]
                ctx.emit(DataEnvelope(type_key=key, payload=normalized, metadata=env.metadata))


class EmaIndicator:
    def compute(self, ctx: PipelineContext) -> None:
        ohlc = ctx.optional("ohlc")
        if ohlc:
            closes = [bar["close"] for bar in ohlc.payload]
            ema = sum(closes[-min(20, len(closes)):]) / min(20, len(closes)) if closes else 0.0
            ctx.emit(DataEnvelope(type_key="ema", payload={"ema20": ema}))


class BosChoChAnalyzer:
    def analyze(self, ctx: PipelineContext) -> None:
        ctx.emit(DataEnvelope(type_key="market_structure", payload={"bos": [], "choch": []}))


class DirectionLabel:
    def generate(self, ctx: PipelineContext) -> None:
        ctx.emit(DataEnvelope(type_key="labels", payload={"direction": "neutral"}))


class CandleObservation:
    def build(self, ctx: PipelineContext) -> dict:
        klines = ctx.optional("klines")
        obs = {"candles": klines.payload if klines else []}
        ctx.emit(DataEnvelope(type_key="observation", payload=obs))
        return obs


class ProfitReward:
    def calculate(self, ctx: PipelineContext) -> float:
        pnl = ctx.optional("pnl")
        return float(pnl.payload) if pnl else 0.0


class DiscreteAction:
    def sample(self, ctx: PipelineContext) -> str:
        return "hold"

    def apply(self, ctx: PipelineContext, action: Any) -> None:
        ctx.emit(DataEnvelope(type_key="action", payload=action))


class SpotEnvironment:
    def reset(self) -> dict:
        return {"balance": 10000.0}

    def step(self, action: Any) -> tuple[dict, float, bool, dict]:
        return {"balance": 10000.0}, 0.0, False, {}


class RuleBasedStrategy:
    def on_bar(self, ctx: PipelineContext) -> None:
        pass

    def signals(self, ctx: PipelineContext) -> list[Any]:
        return []


class SimulationExecution:
    def execute_order(self, ctx: PipelineContext, order: Any) -> dict:
        return {"status": "filled", "order": order}


class FixedRisk:
    def check(self, ctx: PipelineContext, order: Any) -> bool:
        return True

    def position_size(self, ctx: PipelineContext) -> float:
        return 0.01


class SingleAssetPortfolio:
    def __init__(self) -> None:
        self._positions: dict[str, Any] = {}

    def update(self, ctx: PipelineContext) -> None:
        pass

    def positions(self) -> dict[str, Any]:
        return dict(self._positions)


class BinanceExchange:
    def fetch_ticker(self, symbol: str) -> dict:
        return {"symbol": symbol, "price": 0.0}

    def fetch_ohlcv(self, symbol: str, timeframe: str) -> list:
        return []


class PaperBroker:
    def submit_order(self, order: Any) -> dict:
        return {"order_id": "paper-1", "status": "submitted"}

    def cancel_order(self, order_id: str) -> bool:
        return True


class UniformReplayBuffer:
    def __init__(self) -> None:
        self._buffer: list = []

    def add(self, transition: Any) -> None:
        self._buffer.append(transition)

    def sample(self, batch_size: int) -> list:
        return self._buffer[:batch_size]


class PpoAlgorithm:
    def train_step(self, batch: list) -> dict:
        return {"loss": 0.0, "batch_size": len(batch)}


class StandardRlTraining:
    def run(self, config: dict) -> dict:
        return {"status": "completed", "epochs": config.get("epochs", 1)}


class WalkForwardEval:
    def evaluate(self, model: Any, data: Any) -> dict:
        return {"score": 0.0}


class EventDrivenBacktest:
    def run(self, strategy: Any, data: Any) -> dict:
        return {"pnl": 0.0, "trades": 0}


class PaperTradingEngine:
    def start(self) -> None:
        pass

    def stop(self) -> dict:
        return {"status": "stopped"}


class LiveTradingEngine:
    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass


class EquityCurveViz:
    def render(self, ctx: PipelineContext) -> dict:
        return {"type": "equity_curve"}


class SlackNotification:
    def send(self, message: str, *, channel: str = "default") -> bool:
        return True


class StructlogMonitoring:
    def record_metric(self, name: str, value: float, tags: dict | None = None) -> None:
        pass


class SchemaConfiguration:
    def validate(self, config: dict) -> dict:
        return config


DOMAIN_PLUGINS: list[tuple[str, PluginMetadata, Callable[..., Any]]] = [
    ("platform.normalizations", _meta("symbol_normalizer", "platform.normalizations"), lambda **kw: SymbolNormalizer()),
    ("platform.indicators", _meta("ema_indicator", "platform.indicators"), lambda **kw: EmaIndicator()),
    ("platform.market_structures", _meta("bos_choch", "platform.market_structures"), lambda **kw: BosChoChAnalyzer()),
    ("platform.labels", _meta("direction_label", "platform.labels"), lambda **kw: DirectionLabel()),
    ("platform.observations", _meta("candle_observation", "platform.observations"), lambda **kw: CandleObservation()),
    ("platform.rewards", _meta("profit_reward", "platform.rewards"), lambda **kw: ProfitReward()),
    ("platform.actions", _meta("discrete_action", "platform.actions"), lambda **kw: DiscreteAction()),
    ("platform.environments", _meta("spot_env", "platform.environments"), lambda **kw: SpotEnvironment()),
    ("platform.strategies", _meta("rule_based", "platform.strategies"), lambda **kw: RuleBasedStrategy()),
    ("platform.executions", _meta("simulation_execution", "platform.executions"), lambda **kw: SimulationExecution()),
    ("platform.risks", _meta("fixed_risk", "platform.risks"), lambda **kw: FixedRisk()),
    ("platform.portfolios", _meta("single_asset", "platform.portfolios"), lambda **kw: SingleAssetPortfolio()),
    ("platform.exchanges", _meta("binance_exchange", "platform.exchanges"), lambda **kw: BinanceExchange()),
    ("platform.brokers", _meta("paper_broker", "platform.brokers"), lambda **kw: PaperBroker()),
    ("platform.replay_buffers", _meta("uniform_buffer", "platform.replay_buffers"), lambda **kw: UniformReplayBuffer()),
    ("platform.rl_algorithms", _meta("ppo", "platform.rl_algorithms"), lambda **kw: PpoAlgorithm()),
    ("platform.training_pipelines", _meta("standard_rl_train", "platform.training_pipelines"), lambda **kw: StandardRlTraining()),
    ("platform.evaluation_pipelines", _meta("walk_forward", "platform.evaluation_pipelines"), lambda **kw: WalkForwardEval()),
    ("platform.backtesting", _meta("event_driven", "platform.backtesting"), lambda **kw: EventDrivenBacktest()),
    ("platform.paper_trading", _meta("paper_engine", "platform.paper_trading"), lambda **kw: PaperTradingEngine()),
    ("platform.live_trading", _meta("live_engine", "platform.live_trading"), lambda **kw: LiveTradingEngine()),
    ("platform.visualizations", _meta("equity_curve", "platform.visualizations"), lambda **kw: EquityCurveViz()),
    ("platform.notifications", _meta("slack_notifier", "platform.notifications"), lambda **kw: SlackNotification()),
    ("platform.monitoring", _meta("structlog_monitoring", "platform.monitoring"), lambda **kw: StructlogMonitoring()),
    ("platform.configurations", _meta("schema_config", "platform.configurations"), lambda **kw: SchemaConfiguration()),
]


def register_all_domain_plugins(manager: PluginManager) -> int:
    count = 0
    for group, meta, factory in DOMAIN_PLUGINS:
        reg = GROUP_REGISTRY_MAP.get(group) or manager.registry(group)
        if meta.name not in {m.name for m in reg.list_plugins()}:
            reg.register(meta, factory)
            count += 1
    return count
