"""G31 — bounded probabilistic hint outputs."""

from __future__ import annotations

import pytest

from quant_platform.rl_product.perception.pipeline import DEFAULT_HINT_COMPUTERS, PerceptionPipeline
from tests.platform.rl_product.g31.conftest import trending_bars


@pytest.mark.parametrize("name", list(DEFAULT_HINT_COMPUTERS.keys()))
def test_hint_outputs_bounded(name: str):
    bars = trending_bars(80)
    pipeline = PerceptionPipeline()
    for t in (10, 40, 79):
        env = pipeline.compute_hints(bars, t)[name]
        assert 0.0 <= env.value <= 1.0, f"{name} at t={t} out of range: {env.value}"
        assert env.metadata.get("level") is None
        assert env.metadata.get("price") is None


def test_compressor_dims_16_and_32():
    bars = trending_bars(50)
    pipeline16 = PerceptionPipeline(context_dims=16)
    pipeline32 = PerceptionPipeline(context_dims=32)
    hints = {name: env.value for name, env in pipeline16.compute_hints(bars, 49).items()}
    vec16 = pipeline16.compressor.compress(bars, hints)
    vec32 = pipeline32.compressor.compress(bars, hints)
    assert len(vec16) == 16
    assert len(vec32) == 32
    assert all(0.0 <= v <= 1.0 for v in vec16)
    assert all(0.0 <= v <= 1.0 for v in vec32)
