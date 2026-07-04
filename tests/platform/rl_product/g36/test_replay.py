"""G36 — deterministic episode replay."""

from __future__ import annotations

from quant_platform.rl_product.evaluation.replay import assert_deterministic_replay, replay_observation_sequence
from quant_platform.rl_product.graph import RLProductGraph
from tests.platform.rl_product.g36.conftest import eval_config, make_episode


def test_replay_same_seed_same_observations():
    episode = make_episode(35)
    graph = RLProductGraph.compile(eval_config())
    first = replay_observation_sequence(episode, graph, seed=99)
    second = replay_observation_sequence(episode, graph, seed=99)
    assert first == second
    assert len(first) > 1


def test_assert_deterministic_replay():
    episode = make_episode(30)
    graph = RLProductGraph.compile(eval_config())
    result = assert_deterministic_replay(episode, graph, seed=7)
    assert result["deterministic"] is True
    assert result["obs_dim"] == 128
