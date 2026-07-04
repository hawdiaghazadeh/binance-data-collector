"""G36 — context leakage checks."""

from __future__ import annotations

import pytest

from quant_platform.rl_product.evaluation.ablation import LeakageChecker, LeakageConfig, context_sharpe_uplift_pct
from quant_platform.rl_product.evaluation.metrics import EvalMetrics


def test_context_uplift_pct():
    price_only = EvalMetrics(sharpe=1.0)
    full = EvalMetrics(sharpe=1.1)
    assert context_sharpe_uplift_pct(price_only, full) == pytest.approx(10.0)


def test_leakage_checker_pass():
    checker = LeakageChecker(LeakageConfig(max_context_sharpe_uplift_pct=15))
    result = checker.check(
        price_only=EvalMetrics(sharpe=0.5, max_drawdown=0.1, trade_count=20),
        full_context=EvalMetrics(sharpe=0.55, max_drawdown=0.12, trade_count=22),
        context_only=EvalMetrics(sharpe=-0.2, max_drawdown=0.25, trade_count=1),
        context_only_entropy=0.005,
    )
    assert result["context_uplift_pass"] is True
    assert result["context_only_pass"] is True
    assert result["context_only_no_trade_signal"] is True
    assert result["all_pass"] is True


def test_leakage_checker_fails_on_high_uplift():
    checker = LeakageChecker(LeakageConfig(max_context_sharpe_uplift_pct=15))
    result = checker.check(
        price_only=EvalMetrics(sharpe=0.5, max_drawdown=0.1, trade_count=20),
        full_context=EvalMetrics(sharpe=1.0, max_drawdown=0.12, trade_count=22),
        context_only=EvalMetrics(sharpe=-0.1, max_drawdown=0.3, trade_count=1),
    )
    assert result["context_uplift_pass"] is False
    assert result["all_pass"] is False
