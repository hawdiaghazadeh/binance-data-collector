"""G33 — reward engine PnL-dominant with context gate off."""

from __future__ import annotations

import pytest

from quant_platform.rl_product.env.portfolio import PortfolioTracker
from quant_platform.rl_product.env.reward import RewardConfig, RewardEngine


def test_context_gate_off_reward_is_pnl_and_risk_only():
    engine = RewardEngine(
        RewardConfig(max_context_reward_weight=0.0, context_gate=False)
    )
    portfolio = PortfolioTracker.initial(market="spot", initial_equity=10_000.0)
    portfolio.peak_equity = 10_000.0
    portfolio._prev_equity = 10_000.0
    reward, components = engine.compute(step_pnl=100.0, portfolio=portfolio, hint_conf=0.9)
    assert components["context"] == 0.0
    assert components["pnl"] == pytest.approx(0.01)
    assert reward == pytest.approx(components["pnl"] + components["risk"])


def test_max_context_reward_weight_capped():
    with pytest.raises(ValueError, match="0.08"):
        RewardConfig(max_context_reward_weight=0.09)


def test_context_reward_only_on_positive_pnl():
    engine = RewardEngine(RewardConfig(max_context_reward_weight=0.05, context_gate=True))
    portfolio = PortfolioTracker.initial(market="spot", initial_equity=10_000.0)
    portfolio._prev_equity = 10_000.0
    _, neg = engine.compute(step_pnl=-50.0, portfolio=portfolio, hint_conf=0.9)
    assert neg["context"] == 0.0
    _, pos = engine.compute(step_pnl=100.0, portfolio=portfolio, hint_conf=0.9)
    assert pos["context"] > 0.0
