"""G34 — PPO trainer gradient and update."""

from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")

from quant_platform.rl_product.agent.buffer import RolloutBatch
from quant_platform.rl_product.agent.ppo import PPOTrainer
from tests.platform.rl_product.g34.conftest import default_agent_config, schema_from_config


def _synthetic_batch(steps: int = 16, obs_dim: int = 128) -> RolloutBatch:
    obs = torch.randn(steps, obs_dim)
    actions = torch.randn(steps, 1)
    log_probs = torch.randn(steps)
    rewards = torch.randn(steps) * 0.01
    values = torch.randn(steps)
    dones = torch.zeros(steps)
    dones[-1] = 1.0
    return RolloutBatch(
        observations=obs,
        actions=actions,
        log_probs=log_probs,
        rewards=rewards,
        values=values,
        dones=dones,
    )


def test_ppo_update_produces_nonzero_grad_and_finite_loss():
    config = default_agent_config()
    trainer = PPOTrainer.from_schema(schema_from_config(config), config)
    batch = _synthetic_batch()
    metrics = trainer.update(batch)
    assert metrics["loss"] == pytest.approx(metrics["loss"])
    assert metrics["grad_norm"] > 0.0


def test_advantage_normalization_zero_mean():
    config = default_agent_config()
    trainer = PPOTrainer.from_schema(schema_from_config(config), config)
    batch = _synthetic_batch()
    batch = trainer.compute_advantages(batch)
    assert float(batch.advantages.mean()) == pytest.approx(0.0, abs=1e-5)
