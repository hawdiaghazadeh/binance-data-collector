"""Phase 15 RL core tests."""

from __future__ import annotations

import pytest

from quant_platform.core.manager import PluginManager
from quant_platform.replay_buffers.uniform import UniformReplayBufferEngine
from quant_platform.rl_algorithms.ppo import ppo_train_step
from quant_platform.rl_algorithms.sac import sac_train_step
from quant_platform.rl_core.pipeline import RLCorePipelineBuilder, register_rl_core_plugins
from quant_platform.training_pipelines.loop import run_training_loop


def _transitions(count: int) -> list[dict]:
    return [
        {
            "state": {"step": index},
            "action": "buy" if index % 2 == 0 else "hold",
            "reward": float(index),
            "next_state": {"step": index + 1},
            "done": index == count - 1,
        }
        for index in range(count)
    ]


class TestRLCoreCompute:
    def test_uniform_buffer_sample(self):
        buffer = UniformReplayBufferEngine(capacity=10)
        for transition in _transitions(5):
            buffer.add(transition)
        batch = buffer.sample(3)
        assert len(batch) == 3
        assert all("reward" in item for item in batch)

    def test_ppo_train_step(self):
        metrics = ppo_train_step(_transitions(4))
        assert metrics["batch_size"] == 4
        assert "policy_loss" in metrics
        assert ppo_train_step([])["loss"] == 0.0

    def test_sac_train_step(self):
        metrics = sac_train_step(_transitions(4))
        assert metrics["batch_size"] == 4
        assert "actor_loss" in metrics
        assert "critic_loss" in metrics

    def test_run_training_loop(self):
        buffer = UniformReplayBufferEngine(capacity=100)
        metrics = run_training_loop(
            {"epochs": 2, "batch_size": 2, "transitions": _transitions(8)},
            buffer=buffer,
            algorithm=type("Algo", (), {"train_step": staticmethod(ppo_train_step)})(),
        )
        assert metrics["status"] == "completed"
        assert metrics["epochs"] == 2
        assert len(metrics["steps"]) == 2
        assert metrics["buffer_size"] == 8


class TestRLCoreRegistry:
    def test_uniform_buffer_plugin(self):
        manager = PluginManager()
        register_rl_core_plugins(manager)
        buffer = manager.get("platform.replay_buffers", "uniform_buffer")
        assert buffer.sample(1) == []
        buffer.add(_transitions(1)[0])
        assert len(buffer.sample(1)) == 1

    def test_ppo_plugin(self):
        manager = PluginManager()
        register_rl_core_plugins(manager)
        algo = manager.get("platform.rl_algorithms", "ppo")
        assert algo.train_step([])["loss"] == 0.0
        step = algo.train_step(_transitions(3))
        assert step["batch_size"] == 3

    def test_sac_plugin(self):
        manager = PluginManager()
        register_rl_core_plugins(manager)
        algo = manager.get("platform.rl_algorithms", "sac")
        step = algo.train_step(_transitions(2))
        assert step["batch_size"] == 2

    def test_standard_rl_train_plugin(self):
        manager = PluginManager()
        register_rl_core_plugins(manager)
        train = manager.get("platform.training_pipelines", "standard_rl_train")
        result = train.run({"epochs": 1, "transitions": _transitions(4), "batch_size": 2})
        assert result["status"] == "completed"
        assert result["buffer_size"] == 4

    def test_rl_core_pipeline_with_sac(self):
        manager = PluginManager()
        register_rl_core_plugins(manager)
        builder = RLCorePipelineBuilder(manager)
        result = builder.run(
            {
                "epochs": 3,
                "batch_size": 2,
                "transitions": _transitions(6),
            },
            algorithm_name="sac",
        )
        assert result["status"] == "completed"
        assert len(result["steps"]) == 3
        assert "actor_loss" in result["steps"][0]
