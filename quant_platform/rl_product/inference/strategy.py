"""RL policy strategy — StrategyProtocol adapter (G37)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.rl_product.env.portfolio import PortfolioTracker
from quant_platform.rl_product.inference.bars import resolve_klines
from quant_platform.rl_product.inference.policy_inference import PolicyInferenceEngine


def action_to_signal(action: float, *, market: str) -> dict[str, Any]:
    """Map continuous RL action to backtest-compatible signal."""
    if market == "spot":
        target = max(0.0, min(1.0, action))
        if target > 0.05:
            return {"side": "buy", "size": target, "reason": "rl_policy", "action": target}
        if target <= 0.02:
            return {"side": "sell", "size": 1.0, "reason": "rl_policy_flat", "action": target}
        return {"side": "hold", "size": 0.0, "reason": "rl_policy_hold", "action": target}

    if action > 0.05:
        size = min(abs(action), 1.0)
        return {"side": "buy", "size": size, "reason": "rl_policy_long", "action": action}
    if action < -0.05:
        size = min(abs(action), 1.0)
        return {"side": "sell", "size": size, "reason": "rl_policy_short", "action": action}
    return {"side": "hold", "size": 0.0, "reason": "rl_policy_hold", "action": action}


class PolicyStrategy:
    """StrategyProtocol — on_bar → obs → policy → signal."""

    def __init__(
        self,
        engine: PolicyInferenceEngine,
        *,
        market: str | None = None,
        initial_equity: float | None = None,
        leverage: float | None = None,
        kill_switch_gate: float | None = None,
    ) -> None:
        config = engine.graph.config
        training = config.get("training", config)
        deploy = config.get("deploy", {})
        if deploy.get("live_approved") is False and kill_switch_gate is None:
            pass
        self._engine = engine
        self._market = market or str(training.get("market", "spot"))
        self._initial_equity = float(initial_equity or training.get("initial_equity", 10_000.0))
        self._leverage = float(leverage or training.get("leverage", 1.0))
        perception = config.get("perception", {})
        self._master_gate = float(
            kill_switch_gate if kill_switch_gate is not None else perception.get("master_gate", 1.0)
        )
        self._portfolio = PortfolioTracker.initial(
            market=self._market,
            initial_equity=self._initial_equity,
            leverage=self._leverage if self._market == "futures" else 1.0,
        )
        self._last_signals: list[dict[str, Any]] = []

    @property
    def engine(self) -> PolicyInferenceEngine:
        return self._engine

    @property
    def graph_schema_hash(self) -> str:
        return self._engine.graph_schema_hash

    def on_bar(self, ctx: PipelineContext) -> None:
        self._last_signals = [self._decide(ctx)]
        ctx.emit(DataEnvelope(type_key="strategy_signals", payload=list(self._last_signals)))

    def signals(self, ctx: PipelineContext) -> list[Any]:
        if self._last_signals:
            return list(self._last_signals)
        return [self._decide(ctx)]

    def _decide(self, ctx: PipelineContext) -> dict[str, Any]:
        training = self._engine.graph.config.get("training", self._engine.graph.config)
        symbol = str(training.get("symbol", "BTCUSDT"))
        timeframe = str(training.get("timeframe", "1h"))
        bars = resolve_klines(ctx, symbol=symbol, timeframe=timeframe)
        if len(bars) < 2:
            return {"side": "hold", "size": 0.0, "reason": "warmup"}

        t = len(bars) - 1
        price = bars[t].close
        obs = self._engine.build_observation(
            bars,
            t,
            self._portfolio.to_dict(price),
            price=price,
        )
        zero_context = self._master_gate <= 0.0
        action = self._engine.act(obs, deterministic=True, zero_context=zero_context)
        signal = action_to_signal(action, market=self._market)
        signal["graph_schema_hash"] = self._engine.graph_schema_hash
        return signal
