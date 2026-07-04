"""G34 agent test helpers."""

from __future__ import annotations

from quant_platform.rl_product.observation.schema import ObservationSchema


def default_agent_config(**overrides) -> dict:
    cfg = {
        "training": {"market": "futures"},
        "observation": {"dim": 128, "context_dims": 16, "schema_version": "1.0"},
        "agent": {
            "price_trunk_hidden": [64, 32],
            "context_trunk_hidden": [16, 8],
            "portfolio_trunk_hidden": [16, 8],
            "learning_rate": 3e-4,
            "clip_ratio": 0.2,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "entropy_coef": 0.01,
            "max_grad_norm": 0.5,
            "ppo_epochs": 2,
        },
    }
    cfg.update(overrides)
    return cfg


def schema_from_config(config: dict | None = None) -> ObservationSchema:
    schema = ObservationSchema.from_config(config or default_agent_config())
    schema.validate_budget()
    return schema
