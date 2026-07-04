"""Phase 10 action registry tests."""

from __future__ import annotations

import pytest

from quant_platform.actions.continuous import sample_continuous_action
from quant_platform.actions.discrete import sample_discrete_action
from quant_platform.actions.hybrid import sample_hybrid_action
from quant_platform.actions.pipeline import ActionPipelineBuilder, register_action_plugins
from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.manager import PluginManager


class _DeterministicRNG:
    def __init__(self, value: float = 0.95) -> None:
        self._value = value

    def random(self) -> float:
        return self._value

    def choice(self, seq):
        return seq[0]

    def gauss(self, _mu: float, _sigma: float) -> float:
        return 0.0


class TestActionCompute:
    def test_sample_discrete_from_policy(self):
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="policy_probs", payload=[0.1, 0.2, 0.7]))
        action = sample_discrete_action(ctx, exploration=0.0, rng=_DeterministicRNG(0.95))
        assert action == "sell"

    def test_sample_discrete_from_signal(self):
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="strategy_signals", payload=[{"side": "buy"}]))
        action = sample_discrete_action(ctx)
        assert action == "buy"

    def test_sample_continuous_from_policy(self):
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="policy_mean", payload=0.75))
        value = sample_continuous_action(ctx, low=-1.0, high=1.0)
        assert value == 0.75

    def test_sample_continuous_clamps(self):
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="policy_mean", payload=2.0))
        value = sample_continuous_action(ctx, low=-1.0, high=1.0)
        assert value == 1.0

    def test_sample_hybrid_hold(self):
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="action_override", payload="hold"))
        action = sample_hybrid_action(ctx)
        assert action == {"side": "hold", "size": 0.0}

    def test_sample_hybrid_buy_with_size(self):
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="action_override", payload="buy"))
        ctx.emit(DataEnvelope(type_key="policy_mean", payload=0.6))
        action = sample_hybrid_action(ctx)
        assert action["side"] == "buy"
        assert action["size"] == pytest.approx(0.6)


class TestActionRegistry:
    def test_discrete_action_plugin(self):
        manager = PluginManager()
        register_action_plugins(manager)
        plugin = manager.get(
            "platform.actions",
            "discrete_action",
            config={"exploration": 0.0, "seed": 0},
        )
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="action_override", payload="buy"))
        action = plugin.sample(ctx)
        plugin.apply(ctx, action)
        payload = ctx.require("action").payload
        assert action == "buy"
        assert payload["space"] == "discrete"
        assert payload["value"] == "buy"

    def test_continuous_action_plugin(self):
        manager = PluginManager()
        register_action_plugins(manager)
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="policy_mean", payload=-0.25))
        plugin = manager.get("platform.actions", "continuous_action")
        action = plugin.sample(ctx)
        plugin.apply(ctx, action)
        assert ctx.require("action").payload["value"] == -0.25

    def test_hybrid_action_plugin(self):
        manager = PluginManager()
        register_action_plugins(manager)
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="action_override", payload="sell"))
        ctx.emit(DataEnvelope(type_key="policy_mean", payload=0.4))
        plugin = manager.get("platform.actions", "hybrid_action")
        action = plugin.sample(ctx)
        plugin.apply(ctx, action)
        payload = ctx.require("action").payload
        assert payload["space"] == "hybrid"
        assert payload["side"] == "sell"
        assert payload["size"] == pytest.approx(0.4)

    def test_action_pipeline(self):
        manager = PluginManager()
        register_action_plugins(manager)
        builder = ActionPipelineBuilder(manager)
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="policy_probs", payload=[0.0, 0.0, 1.0]))
        ctx.emit(DataEnvelope(type_key="action_override", payload="sell"))
        action = builder.run(ctx, "discrete_action")
        assert action == "sell"
        assert ctx.require("action").payload["value"] == "sell"

    def test_invalid_discrete_apply_raises(self):
        manager = PluginManager()
        register_action_plugins(manager)
        plugin = manager.get("platform.actions", "discrete_action")
        with pytest.raises(ValueError, match="Invalid discrete action"):
            plugin.apply(PipelineContext(), "invalid")
