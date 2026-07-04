"""G35 — short online training run."""

from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")

from quant_platform.rl_product.training.loop import OnlineTrainingLoop
from tests.platform.rl_product.g35.conftest import make_episode, train_config


def test_short_training_run():
    episodes = [make_episode(30, episode_id="a"), make_episode(30, episode_id="b", vol_scale=0.5)]
    config = train_config()
    loop = OnlineTrainingLoop.compile(config, episodes)
    metrics = loop.run(total_timesteps=32)
    assert metrics.timesteps >= 32
    assert metrics.updates >= 1
    assert metrics.last_loss == metrics.last_loss
    assert loop.graph_schema_hash


def test_entropy_coef_decreases_during_training():
    from quant_platform.rl_product.agent.ppo import PPOTrainer
    from quant_platform.rl_product.observation.schema import ObservationSchema

    config = train_config()
    schema = ObservationSchema.from_config(config)
    trainer = PPOTrainer.from_schema(schema, config)
    loop = OnlineTrainingLoop.compile(config, [make_episode()], trainer=trainer)
    loop.run(total_timesteps=32)
    assert trainer.config.entropy_coef <= 0.01
