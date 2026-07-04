"""G36 — evaluation metrics."""

from __future__ import annotations

import pytest

from quant_platform.rl_product.evaluation.metrics import (
    compute_max_drawdown,
    compute_win_rate,
    summarize_equity_curve,
)


def test_summarize_equity_curve():
    equity = [10_000.0, 10_100.0, 10_050.0, 10_200.0]
    metrics = summarize_equity_curve(equity, trade_count=3)
    assert metrics.steps == 3
    assert metrics.trade_count == 3
    assert 0.0 <= metrics.win_rate <= 1.0
    assert metrics.max_drawdown >= 0.0


def test_max_drawdown():
    equity = [100.0, 110.0, 90.0, 95.0]
    dd = compute_max_drawdown(equity)
    assert dd == pytest.approx(0.181818, rel=1e-3)


def test_win_rate():
    assert compute_win_rate([0.01, -0.02, 0.03]) == pytest.approx(2 / 3)
