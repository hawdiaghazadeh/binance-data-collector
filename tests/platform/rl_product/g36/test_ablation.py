"""G36 — ablation runner."""

from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")

from quant_platform.rl_product.evaluation.ablation import AblationRunner
from quant_platform.rl_product.graph import RLProductGraph
from tests.platform.rl_product.g36.conftest import eval_config, make_episode, make_episode_set


def test_ablation_runner_variants():
    episodes = make_episode_set(6, bar_count=25)
    config = eval_config()
    result = AblationRunner().run(config, episodes, include_context_only=True)
    assert "price_only" in result["variants"]
    assert "full_context" in result["variants"]
    assert "gate_sweep" in result["variants"]
    assert "context_only" in result["variants"]
    assert "leakage" in result
    assert "all_pass" in result["leakage"]


def test_context_only_zeros_price_block():
    config = eval_config()
    config.setdefault("evaluation", {}).setdefault("ablation", {})["context_only"] = True
    config.setdefault("observation", {})["test_mode"] = True
    episode = make_episode(35)
    graph = RLProductGraph.compile(config)
    builder = graph.observation
    obs = builder.build(episode.bars, 10, config=config)
    price = obs.block("price_action")
    assert all(v == 0.0 for v in price)
