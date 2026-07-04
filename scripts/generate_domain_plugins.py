"""One-off generator for domain plugin packages (G8)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "quant_platform" / "plugins" / "domain"

PLUGIN_SPECS: list[dict[str, str]] = [
    {
        "pkg": "symbol_normalizer",
        "group": "platform.normalizations",
        "class_name": "SymbolNormalizer",
        "imports": "from quant_platform.core.context import DataEnvelope, PipelineContext",
        "body": """
    def normalize(self, ctx: PipelineContext) -> None:
        for key in list(ctx.keys()):
            env = ctx.require(key)
            if isinstance(env.payload, list) and env.payload and isinstance(env.payload[0], dict):
                normalized = [
                    {**row, "symbol": str(row.get("symbol", "")).upper()} for row in env.payload
                ]
                ctx.emit(DataEnvelope(type_key=key, payload=normalized, metadata=env.metadata))
""",
    },
    {
        "pkg": "ema_indicator",
        "group": "platform.indicators",
        "class_name": "EmaIndicator",
        "imports": "from quant_platform.core.context import DataEnvelope, PipelineContext",
        "body": """
    def compute(self, ctx: PipelineContext) -> None:
        ohlc = ctx.optional("ohlc")
        if ohlc:
            closes = [bar["close"] for bar in ohlc.payload]
            ema = sum(closes[-min(20, len(closes)):]) / min(20, len(closes)) if closes else 0.0
            ctx.emit(DataEnvelope(type_key="ema", payload={"ema20": ema}))
""",
    },
    {
        "pkg": "bos_choch",
        "group": "platform.market_structures",
        "class_name": "BosChoChAnalyzer",
        "imports": "from quant_platform.core.context import DataEnvelope, PipelineContext",
        "body": """
    def analyze(self, ctx: PipelineContext) -> None:
        ctx.emit(DataEnvelope(type_key="market_structure", payload={"bos": [], "choch": []}))
""",
    },
    {
        "pkg": "direction_label",
        "group": "platform.labels",
        "class_name": "DirectionLabel",
        "imports": "from quant_platform.core.context import DataEnvelope, PipelineContext",
        "body": """
    def generate(self, ctx: PipelineContext) -> None:
        ctx.emit(DataEnvelope(type_key="labels", payload={"direction": "neutral"}))
""",
    },
    {
        "pkg": "candle_observation",
        "group": "platform.observations",
        "class_name": "CandleObservation",
        "imports": "from quant_platform.core.context import DataEnvelope, PipelineContext",
        "body": """
    def build(self, ctx: PipelineContext) -> dict:
        klines = ctx.optional("klines")
        obs = {"candles": klines.payload if klines else []}
        ctx.emit(DataEnvelope(type_key="observation", payload=obs))
        return obs
""",
    },
    {
        "pkg": "profit_reward",
        "group": "platform.rewards",
        "class_name": "ProfitReward",
        "imports": "from quant_platform.core.context import PipelineContext",
        "body": """
    def calculate(self, ctx: PipelineContext) -> float:
        pnl = ctx.optional("pnl")
        return float(pnl.payload) if pnl else 0.0
""",
    },
    {
        "pkg": "discrete_action",
        "group": "platform.actions",
        "class_name": "DiscreteAction",
        "imports": "from typing import Any\nfrom quant_platform.core.context import DataEnvelope, PipelineContext",
        "body": """
    def sample(self, ctx: PipelineContext) -> str:
        return "hold"

    def apply(self, ctx: PipelineContext, action: Any) -> None:
        ctx.emit(DataEnvelope(type_key="action", payload=action))
""",
    },
    {
        "pkg": "spot_env",
        "group": "platform.environments",
        "class_name": "SpotEnvironment",
        "imports": "from typing import Any",
        "body": """
    def reset(self) -> dict:
        return {"balance": 10000.0}

    def step(self, action: Any) -> tuple[dict, float, bool, dict]:
        return {"balance": 10000.0}, 0.0, False, {}
""",
    },
    {
        "pkg": "rule_based",
        "group": "platform.strategies",
        "class_name": "RuleBasedStrategy",
        "imports": "from typing import Any\nfrom quant_platform.core.context import PipelineContext",
        "body": """
    def on_bar(self, ctx: PipelineContext) -> None:
        pass

    def signals(self, ctx: PipelineContext) -> list[Any]:
        return []
""",
    },
    {
        "pkg": "simulation_execution",
        "group": "platform.executions",
        "class_name": "SimulationExecution",
        "imports": "from typing import Any\nfrom quant_platform.core.context import PipelineContext",
        "body": """
    def execute_order(self, ctx: PipelineContext, order: Any) -> dict:
        return {"status": "filled", "order": order}
""",
    },
    {
        "pkg": "fixed_risk",
        "group": "platform.risks",
        "class_name": "FixedRisk",
        "imports": "from typing import Any\nfrom quant_platform.core.context import PipelineContext",
        "body": """
    def check(self, ctx: PipelineContext, order: Any) -> bool:
        return True

    def position_size(self, ctx: PipelineContext) -> float:
        return 0.01
""",
    },
    {
        "pkg": "single_asset",
        "group": "platform.portfolios",
        "class_name": "SingleAssetPortfolio",
        "imports": "from typing import Any\nfrom quant_platform.core.context import PipelineContext",
        "body": """
    def __init__(self) -> None:
        self._positions: dict[str, Any] = {}

    def update(self, ctx: PipelineContext) -> None:
        pass

    def positions(self) -> dict[str, Any]:
        return dict(self._positions)
""",
    },
    {
        "pkg": "binance_exchange",
        "group": "platform.exchanges",
        "class_name": "BinanceExchange",
        "imports": "",
        "body": """
    def fetch_ticker(self, symbol: str) -> dict:
        return {"symbol": symbol, "price": 0.0}

    def fetch_ohlcv(self, symbol: str, timeframe: str) -> list:
        return []
""",
    },
    {
        "pkg": "paper_broker",
        "group": "platform.brokers",
        "class_name": "PaperBroker",
        "imports": "from typing import Any",
        "body": """
    def submit_order(self, order: Any) -> dict:
        return {"order_id": "paper-1", "status": "submitted"}

    def cancel_order(self, order_id: str) -> bool:
        return True
""",
    },
    {
        "pkg": "uniform_buffer",
        "group": "platform.replay_buffers",
        "class_name": "UniformReplayBuffer",
        "imports": "from typing import Any",
        "body": """
    def __init__(self) -> None:
        self._buffer: list = []

    def add(self, transition: Any) -> None:
        self._buffer.append(transition)

    def sample(self, batch_size: int) -> list:
        return self._buffer[:batch_size]
""",
    },
    {
        "pkg": "ppo",
        "group": "platform.rl_algorithms",
        "class_name": "PpoAlgorithm",
        "imports": "",
        "body": """
    def train_step(self, batch: list) -> dict:
        return {"loss": 0.0, "batch_size": len(batch)}
""",
    },
    {
        "pkg": "standard_rl_train",
        "group": "platform.training_pipelines",
        "class_name": "StandardRlTraining",
        "imports": "",
        "body": """
    def run(self, config: dict) -> dict:
        return {"status": "completed", "epochs": config.get("epochs", 1)}
""",
    },
    {
        "pkg": "walk_forward",
        "group": "platform.evaluation_pipelines",
        "class_name": "WalkForwardEval",
        "imports": "from typing import Any",
        "body": """
    def evaluate(self, model: Any, data: Any) -> dict:
        return {"score": 0.0}
""",
    },
    {
        "pkg": "event_driven",
        "group": "platform.backtesting",
        "class_name": "EventDrivenBacktest",
        "imports": "from typing import Any",
        "body": """
    def run(self, strategy: Any, data: Any) -> dict:
        return {"pnl": 0.0, "trades": 0}
""",
    },
    {
        "pkg": "paper_engine",
        "group": "platform.paper_trading",
        "class_name": "PaperTradingEngine",
        "imports": "",
        "body": """
    def start(self) -> None:
        pass

    def stop(self) -> dict:
        return {"status": "stopped"}
""",
    },
    {
        "pkg": "live_engine",
        "group": "platform.live_trading",
        "class_name": "LiveTradingEngine",
        "imports": "",
        "body": """
    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass
""",
    },
    {
        "pkg": "equity_curve",
        "group": "platform.visualizations",
        "class_name": "EquityCurveViz",
        "imports": "from quant_platform.core.context import PipelineContext",
        "body": """
    def render(self, ctx: PipelineContext) -> dict:
        return {"type": "equity_curve"}
""",
    },
    {
        "pkg": "slack_notifier",
        "group": "platform.notifications",
        "class_name": "SlackNotification",
        "imports": "",
        "body": """
    def send(self, message: str, *, channel: str = "default") -> bool:
        return True
""",
    },
    {
        "pkg": "structlog_monitoring",
        "group": "platform.monitoring",
        "class_name": "StructlogMonitoring",
        "imports": "",
        "body": """
    def record_metric(self, name: str, value: float, tags: dict | None = None) -> None:
        pass
""",
    },
    {
        "pkg": "schema_config",
        "group": "platform.configurations",
        "class_name": "SchemaConfiguration",
        "imports": "",
        "body": """
    def validate(self, config: dict) -> dict:
        return config
""",
    },
]


def render_plugin(spec: dict[str, str]) -> str:
    pkg = spec["pkg"]
    group = spec["group"]
    class_name = spec["class_name"]
    imports = spec["imports"]
    body = spec["body"].rstrip()
    import_block = f"{imports}\n\n" if imports else ""
    return f'''"""Reference domain plugin: {pkg}."""

from __future__ import annotations

{import_block}from quant_platform.plugins.domain._helpers import attach_factory_metadata, reference_meta

PLUGIN_METADATA = reference_meta("{pkg}", "{group}")


class {class_name}:
{body}


def factory(**kwargs) -> {class_name}:
    return {class_name}()


attach_factory_metadata(factory, PLUGIN_METADATA)
'''


def main() -> None:
    for spec in PLUGIN_SPECS:
        pkg_dir = ROOT / spec["pkg"]
        pkg_dir.mkdir(parents=True, exist_ok=True)
        (pkg_dir / "__init__.py").write_text(render_plugin(spec), encoding="utf-8")
    print(f"Generated {len(PLUGIN_SPECS)} domain plugin packages")


if __name__ == "__main__":
    main()
