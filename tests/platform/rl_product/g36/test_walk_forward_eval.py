"""G36 — short walk-forward RL eval run."""

from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")

from quant_platform.rl_product.evaluation.walk_forward import WalkForwardRLEvaluator
from tests.platform.rl_product.g36.conftest import eval_config, make_episode_set


def test_walk_forward_rl_eval_smoke():
    episodes = make_episode_set(8, bar_count=25)
    config = eval_config()
    result = WalkForwardRLEvaluator().evaluate(config, episodes)
    assert result["folds"] >= 4
    assert "oos_sharpe_mean" in result
    assert "oos_max_drawdown" in result
    assert "oos_win_rate_mean" in result
    assert result["graph_schema_hash"]
    for fold in result["fold_results"]:
        assert "oos_sharpe" in fold
        assert "oos_max_drawdown" in fold
        assert "oos_win_rate" in fold
