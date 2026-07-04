"""G31 — feature gate zeros context when master_gate=0."""

from __future__ import annotations

from quant_platform.plugins.rl.feature_gate import FeatureGatePlugin
from quant_platform.rl_product.perception.gate import FeatureGate, GateConfig
from quant_platform.rl_product.perception.pipeline import PerceptionPipeline
from tests.platform.rl_product.g31.conftest import trending_bars


def test_master_gate_zeros_context_block():
    bars = trending_bars(60)
    pipeline = PerceptionPipeline()
    full = pipeline.step(bars, 59, config={"perception": {"master_gate": 1.0}})
    gated = pipeline.step(bars, 59, config={"perception": {"master_gate": 0.0}})
    assert any(v > 0 for v in full)
    assert all(v == 0.0 for v in gated)


def test_family_gate_scales_smc_slots():
    gate = FeatureGate(GateConfig(master_gate=1.0, gate_smc=0.0, gate_rtm=1.0, gate_ict=1.0))
    context = [1.0] * 16
    out = gate.apply(context)
    assert out[0] == 0.0
    assert out[1] == 0.0
    assert out[2] == 0.0
    assert out[3] == 0.0
    assert out[4] == 1.0


def test_feature_gate_plugin():
    plugin = FeatureGatePlugin()
    raw = [0.5] * 16
    zeroed = plugin.apply(raw, config={"perception": {"master_gate": 0.0}}, context_dims=16)
    assert all(v == 0.0 for v in zeroed)
