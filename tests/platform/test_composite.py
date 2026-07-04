"""Tests for composable domain helpers (G4)."""

from __future__ import annotations

from quant_platform.composite.observation import CompositeObservation
from quant_platform.composite.reward import CompositeReward
from quant_platform.composite.risk import CompositeRisk
from quant_platform.composite.strategy import CompositeStrategy
from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.interfaces.domain import (
    ObservationProtocol,
    RewardProtocol,
    RiskProtocol,
    StrategyProtocol,
)


class _FixedReward:
    def __init__(self, value: float) -> None:
        self._value = value

    def calculate(self, ctx: PipelineContext) -> float:
        return self._value


class _RejectingRisk:
    def check(self, ctx: PipelineContext, order: object) -> bool:
        return False

    def position_size(self, ctx: PipelineContext) -> float:
        return 0.0


class _PermissiveRisk:
    def check(self, ctx: PipelineContext, order: object) -> bool:
        return True

    def position_size(self, ctx: PipelineContext) -> float:
        return 0.05


class _StaticStrategy:
    def __init__(self, name: str, signals: list[dict]) -> None:
        self._name = name
        self._signals = signals
        self.on_bar_calls = 0

    def on_bar(self, ctx: PipelineContext) -> None:
        self.on_bar_calls += 1
        ctx.emit(DataEnvelope(type_key=f"{self._name}_bar", payload=True))

    def signals(self, ctx: PipelineContext) -> list[dict]:
        return list(self._signals)


class _DictObservation:
    def __init__(self, key: str, value: object) -> None:
        self._key = key
        self._value = value

    def build(self, ctx: PipelineContext) -> dict:
        return {self._key: self._value}


class TestCompositeReward:
    def test_weighted_sum(self):
        reward = CompositeReward([(_FixedReward(1.0), 0.5), (_FixedReward(3.0), 0.5)])
        assert reward.calculate(PipelineContext()) == 2.0


class TestCompositeRisk:
    def test_all_checks_must_pass(self):
        risk = CompositeRisk([_PermissiveRisk(), _RejectingRisk()])
        assert risk.check(PipelineContext(), {"side": "buy"}) is False

    def test_position_size_uses_minimum(self):
        risk = CompositeRisk([_PermissiveRisk(), _PermissiveRisk()])
        assert risk.position_size(PipelineContext()) == 0.05


class TestCompositeStrategy:
    def test_on_bar_runs_all_strategies(self):
        first = _StaticStrategy("a", [{"side": "buy"}])
        second = _StaticStrategy("b", [{"side": "sell"}])
        strategy = CompositeStrategy([(first, 1.0), (second, 0.5)])

        ctx = PipelineContext()
        strategy.on_bar(ctx)

        assert first.on_bar_calls == 1
        assert second.on_bar_calls == 1
        assert "a_bar" in ctx.keys()
        assert "b_bar" in ctx.keys()

    def test_signals_merge_with_weights(self):
        first = _StaticStrategy("a", [{"side": "buy"}])
        second = _StaticStrategy("b", [{"side": "sell"}])
        strategy = CompositeStrategy([(first, 1.0), (second, 0.0)])

        signals = strategy.signals(PipelineContext())
        assert signals == [{"side": "buy", "weight": 1.0}]


class TestCompositeObservation:
    def test_build_merges_observation_spaces(self):
        composite = CompositeObservation(
            [
                (_DictObservation("candles", [1, 2]), "market"),
                (_DictObservation("position", {"size": 1}), "portfolio"),
            ]
        )
        ctx = PipelineContext()
        merged = composite.build(ctx)

        assert merged == {
            "market": {"candles": [1, 2]},
            "portfolio": {"position": {"size": 1}},
        }
        assert ctx.require("observation").payload == merged

    def test_protocol_compliance(self):
        assert isinstance(_DictObservation("x", 1), ObservationProtocol)
        assert isinstance(_StaticStrategy("s", []), StrategyProtocol)
