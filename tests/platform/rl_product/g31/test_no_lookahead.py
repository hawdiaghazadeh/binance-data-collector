"""G31 — hints must not use future bars (no lookahead)."""

from __future__ import annotations

from quant_platform.rl_product.perception.pipeline import DEFAULT_HINT_COMPUTERS, PerceptionPipeline
from tests.platform.rl_product.g31.conftest import kline, trending_bars


def test_hint_invariant_to_future_bars():
    base = trending_bars(60)
    pipeline = PerceptionPipeline()
    t = 30
    hints_at_t = pipeline.compute_hints(base, t)

    extended = base + [kline(close=999.0, index=len(base) + i) for i in range(20)]
    hints_extended = pipeline.compute_hints(extended, t)

    for name in DEFAULT_HINT_COMPUTERS:
        assert hints_at_t[name].value == hints_extended[name].value, name


def test_pipeline_step_no_lookahead():
    base = trending_bars(40)
    extended = base + [kline(close=500.0, index=40 + i) for i in range(10)]
    pipeline = PerceptionPipeline()
    ctx_base = pipeline.step(base, 25)
    ctx_extended = pipeline.step(extended, 25)
    assert ctx_base == ctx_extended
