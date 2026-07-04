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


def _attach_meta(factory: Callable[..., Any], meta: PluginMetadata) -> Callable[..., Any]:
    factory.PLUGIN_METADATA = meta  # type: ignore[attr-defined]
    return factory


def symbol_normalizer_factory(**kwargs: Any) -> SymbolNormalizer:
    return SymbolNormalizer()


_attach_meta(symbol_normalizer_factory, _meta("symbol_normalizer", "platform.normalizations"))


def ema_indicator_factory(**kwargs: Any) -> EmaIndicator:
    return EmaIndicator()


_attach_meta(ema_indicator_factory, _meta("ema_indicator", "platform.indicators"))


def bos_choch_factory(**kwargs: Any) -> BosChoChAnalyzer:
    return BosChoChAnalyzer()


_attach_meta(bos_choch_factory, _meta("bos_choch", "platform.market_structures"))


def direction_label_factory(**kwargs: Any) -> DirectionLabel:
    return DirectionLabel()


_attach_meta(direction_label_factory, _meta("direction_label", "platform.labels"))


def candle_observation_factory(**kwargs: Any) -> CandleObservation:
    return CandleObservation()


_attach_meta(candle_observation_factory, _meta("candle_observation", "platform.observations"))


def profit_reward_factory(**kwargs: Any) -> ProfitReward:
    return ProfitReward()


_attach_meta(profit_reward_factory, _meta("profit_reward", "platform.rewards"))


def discrete_action_factory(**kwargs: Any) -> DiscreteAction:
    return DiscreteAction()


_attach_meta(discrete_action_factory, _meta("discrete_action", "platform.actions"))


def spot_env_factory(**kwargs: Any) -> SpotEnvironment:
    return SpotEnvironment()


_attach_meta(spot_env_factory, _meta("spot_env", "platform.environments"))


def rule_based_factory(**kwargs: Any) -> RuleBasedStrategy:
    return RuleBasedStrategy()


_attach_meta(rule_based_factory, _meta("rule_based", "platform.strategies"))


def simulation_execution_factory(**kwargs: Any) -> SimulationExecution:
    return SimulationExecution()


_attach_meta(simulation_execution_factory, _meta("simulation_execution", "platform.executions"))


def fixed_risk_factory(**kwargs: Any) -> FixedRisk:
    return FixedRisk()


_attach_meta(fixed_risk_factory, _meta("fixed_risk", "platform.risks"))


def single_asset_factory(**kwargs: Any) -> SingleAssetPortfolio:
    return SingleAssetPortfolio()


_attach_meta(single_asset_factory, _meta("single_asset", "platform.portfolios"))


def binance_exchange_factory(**kwargs: Any) -> BinanceExchange:
    return BinanceExchange()


_attach_meta(binance_exchange_factory, _meta("binance_exchange", "platform.exchanges"))


def paper_broker_factory(**kwargs: Any) -> PaperBroker:
    return PaperBroker()


_attach_meta(paper_broker_factory, _meta("paper_broker", "platform.brokers"))


def uniform_buffer_factory(**kwargs: Any) -> UniformReplayBuffer:
    return UniformReplayBuffer()


_attach_meta(uniform_buffer_factory, _meta("uniform_buffer", "platform.replay_buffers"))


def ppo_factory(**kwargs: Any) -> PpoAlgorithm:
    return PpoAlgorithm()


_attach_meta(ppo_factory, _meta("ppo", "platform.rl_algorithms"))


def standard_rl_train_factory(**kwargs: Any) -> StandardRlTraining:
    return StandardRlTraining()


_attach_meta(standard_rl_train_factory, _meta("standard_rl_train", "platform.training_pipelines"))


def walk_forward_factory(**kwargs: Any) -> WalkForwardEval:
    return WalkForwardEval()


_attach_meta(walk_forward_factory, _meta("walk_forward", "platform.evaluation_pipelines"))


def event_driven_factory(**kwargs: Any) -> EventDrivenBacktest:
    return EventDrivenBacktest()


_attach_meta(event_driven_factory, _meta("event_driven", "platform.backtesting"))


def paper_engine_factory(**kwargs: Any) -> PaperTradingEngine:
    return PaperTradingEngine()


_attach_meta(paper_engine_factory, _meta("paper_engine", "platform.paper_trading"))


def live_engine_factory(**kwargs: Any) -> LiveTradingEngine:
    return LiveTradingEngine()


_attach_meta(live_engine_factory, _meta("live_engine", "platform.live_trading"))


def equity_curve_factory(**kwargs: Any) -> EquityCurveViz:
    return EquityCurveViz()


_attach_meta(equity_curve_factory, _meta("equity_curve", "platform.visualizations"))


def slack_notifier_factory(**kwargs: Any) -> SlackNotification:
    return SlackNotification()


_attach_meta(slack_notifier_factory, _meta("slack_notifier", "platform.notifications"))


def structlog_monitoring_factory(**kwargs: Any) -> StructlogMonitoring:
    return StructlogMonitoring()


_attach_meta(structlog_monitoring_factory, _meta("structlog_monitoring", "platform.monitoring"))


def schema_config_factory(**kwargs: Any) -> SchemaConfiguration:
    return SchemaConfiguration()


_attach_meta(schema_config_factory, _meta("schema_config", "platform.configurations"))


DOMAIN_PLUGINS: list[tuple[str, PluginMetadata, Callable[..., Any]]] = [
    ("platform.normalizations", symbol_normalizer_factory.PLUGIN_METADATA, symbol_normalizer_factory),
    ("platform.indicators", ema_indicator_factory.PLUGIN_METADATA, ema_indicator_factory),
    ("platform.market_structures", bos_choch_factory.PLUGIN_METADATA, bos_choch_factory),
    ("platform.labels", direction_label_factory.PLUGIN_METADATA, direction_label_factory),
    ("platform.observations", candle_observation_factory.PLUGIN_METADATA, candle_observation_factory),
    ("platform.rewards", profit_reward_factory.PLUGIN_METADATA, profit_reward_factory),
    ("platform.actions", discrete_action_factory.PLUGIN_METADATA, discrete_action_factory),
    ("platform.environments", spot_env_factory.PLUGIN_METADATA, spot_env_factory),
    ("platform.strategies", rule_based_factory.PLUGIN_METADATA, rule_based_factory),
    ("platform.executions", simulation_execution_factory.PLUGIN_METADATA, simulation_execution_factory),
    ("platform.risks", fixed_risk_factory.PLUGIN_METADATA, fixed_risk_factory),
    ("platform.portfolios", single_asset_factory.PLUGIN_METADATA, single_asset_factory),
    ("platform.exchanges", binance_exchange_factory.PLUGIN_METADATA, binance_exchange_factory),
    ("platform.brokers", paper_broker_factory.PLUGIN_METADATA, paper_broker_factory),
    ("platform.replay_buffers", uniform_buffer_factory.PLUGIN_METADATA, uniform_buffer_factory),
    ("platform.rl_algorithms", ppo_factory.PLUGIN_METADATA, ppo_factory),
    ("platform.training_pipelines", standard_rl_train_factory.PLUGIN_METADATA, standard_rl_train_factory),
    ("platform.evaluation_pipelines", walk_forward_factory.PLUGIN_METADATA, walk_forward_factory),
    ("platform.backtesting", event_driven_factory.PLUGIN_METADATA, event_driven_factory),
    ("platform.paper_trading", paper_engine_factory.PLUGIN_METADATA, paper_engine_factory),
    ("platform.live_trading", live_engine_factory.PLUGIN_METADATA, live_engine_factory),
    ("platform.visualizations", equity_curve_factory.PLUGIN_METADATA, equity_curve_factory),
    ("platform.notifications", slack_notifier_factory.PLUGIN_METADATA, slack_notifier_factory),
    ("platform.monitoring", structlog_monitoring_factory.PLUGIN_METADATA, structlog_monitoring_factory),
    ("platform.configurations", schema_config_factory.PLUGIN_METADATA, schema_config_factory),
]


def register_all_domain_plugins(manager: PluginManager) -> int:
    count = 0
    domain_groups = {group for group, _, _ in DOMAIN_PLUGINS}
    for group in domain_groups:
        count += manager.discover(group, scan_packages=[])

    for group, meta, factory in DOMAIN_PLUGINS:
        reg = GROUP_REGISTRY_MAP.get(group) or manager.registry(group)
        if meta.name not in {m.name for m in reg.list_plugins()}:
            reg.register(meta, factory)
            count += 1
    return count
