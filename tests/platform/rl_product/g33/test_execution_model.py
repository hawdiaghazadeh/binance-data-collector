"""G33 — execution model slippage and fees."""

from __future__ import annotations

from quant_platform.rl_product.env.execution import ExecutionConfig, SimpleExecutionModel


def test_slippage_and_spread_worsen_fill_price():
    model = SimpleExecutionModel(ExecutionConfig(fee_bps=10, spread_bps=10, slippage_bps=5))
    fill = model.simulate_fill(
        target_exposure=1.0,
        price=100.0,
        position=0.0,
        equity=10_000.0,
        bar_volume=1000.0,
        market="spot",
    )
    assert fill.delta_position > 0
    assert fill.fill_price > 100.0
    assert fill.fee > 0
    assert fill.spread_cost > 0
    assert fill.slippage_cost > 0


def test_zero_delta_exposure_no_costs():
    model = SimpleExecutionModel()
    fill = model.simulate_fill(
        target_exposure=0.0,
        price=100.0,
        position=0.0,
        equity=10_000.0,
        bar_volume=1000.0,
        market="spot",
    )
    assert fill.delta_position == 0.0
    assert fill.fee == 0.0
