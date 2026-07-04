"""G37 — backtest engine consumes policy_strategy without engine patch."""

from __future__ import annotations

from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

from quant_platform.backtesting.event_driven import run_event_driven_backtest
from quant_platform.plugins.rl.policy_strategy import factory as policy_strategy_factory
from tests.platform.rl_product.g37.conftest import make_kline_rows
from tests.platform.rl_product.g37.test_policy_inference import _train_and_save


def test_backtest_hook_with_policy_strategy(tmp_path: Path):
    ckpt, config = _train_and_save(tmp_path)
    strategy = policy_strategy_factory(checkpoint_path=ckpt, config=config)
    bars = make_kline_rows(35)
    result = run_event_driven_backtest(strategy, bars, initial_cash=10_000.0, fee_rate=0.001)
    assert result["method"] == "event_driven"
    assert "equity_curve" in result
    assert len(result["equity_curve"]) == len(bars) + 1
    assert result["final_equity"] > 0
