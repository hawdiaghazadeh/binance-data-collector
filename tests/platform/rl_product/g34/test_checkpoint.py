"""G34 — checkpoint roundtrip with schema metadata."""

from __future__ import annotations

from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

from quant_platform.rl_product.agent.checkpoint import load_checkpoint, save_checkpoint
from quant_platform.rl_product.agent.network import ActorCriticModule, SplitTrunkActorCritic
from tests.platform.rl_product.g34.conftest import default_agent_config, schema_from_config


def test_checkpoint_roundtrip(tmp_path: Path):
    schema = schema_from_config()
    config = default_agent_config()
    core = SplitTrunkActorCritic(
        schema,
        price_trunk_hidden=(64, 32),
        context_trunk_hidden=(16, 8),
        portfolio_trunk_hidden=(16, 8),
    )
    model = ActorCriticModule(core)
    obs = torch.randn(4, schema.obs_dim)
    before, _, _ = model.act(obs, deterministic=True)

    ckpt = tmp_path / "policy.pt"
    save_checkpoint(ckpt, model, schema=schema, graph_schema_hash="abc123")

    loaded, metadata = load_checkpoint(ckpt, config=config)
    after, _, _ = loaded.act(obs, deterministic=True)

    assert metadata["schema_version"] == "1.0"
    assert metadata["obs_dim"] == 128
    assert metadata["graph_schema_hash"] == "abc123"
    assert torch.allclose(before, after)
