"""G33 — RL environment bridge and graph phases."""

from __future__ import annotations

from quant_platform.rl_product.env.bridge import RLEnvironmentBridge
from quant_platform.rl_product.env.execution import SimpleExecutionModel
from quant_platform.rl_product.graph import RLProductGraph
from tests.platform.rl_product.g33.conftest import default_config, trending_episode


def test_rl_product_graph_compile_and_phases():
    config = default_config()
    graph = RLProductGraph.compile(config)
    assert graph.schema_hash
    assert graph.perception is not None
    assert graph.observation is not None
    assert graph.reward_engine is not None


def test_spot_bridge_reset_and_step():
    episode = trending_episode(30)
    graph = RLProductGraph.compile(default_config())
    bridge = RLEnvironmentBridge(
        episode,
        graph,
        execution=SimpleExecutionModel(),
        market="spot",
    )
    obs, info = bridge.reset()
    assert len(obs) == 128
    assert info["step"] == 0

    total_reward = 0.0
    done = False
    steps = 0
    while not done and steps < 25:
        obs, reward, done, info = bridge.step(0.5)
        total_reward += reward
        steps += 1
        assert len(obs) == 128
        assert "reward_components" in info
        assert "pnl" in info["reward_components"]

    assert steps > 0
    assert info["fee"] >= 0.0


def test_futures_bridge_accepts_short_exposure():
    episode = trending_episode(20)
    graph = RLProductGraph.compile(default_config())
    bridge = RLEnvironmentBridge(
        episode,
        graph,
        market="futures",
        leverage=5.0,
    )
    bridge.reset()
    _, _, _, info = bridge.step(-0.5)
    assert info["market"] == "futures"


def test_master_gate_zero_context_in_obs_via_bridge():
    config = default_config(perception={"master_gate": 0.0})
    episode = trending_episode(40)
    graph = RLProductGraph.compile(config)
    bridge = RLEnvironmentBridge(episode, graph, market="spot")
    bridge.reset()
    obs, _, _, _ = bridge.step(0.3)
    context_start = graph.observation.schema.block_slices()["context"].start
    context_stop = graph.observation.schema.block_slices()["context"].stop
    context = obs[context_start:context_stop]
    assert all(v == 0.0 for v in context)
