"""G34 — context trunk ablation (zeroed context block)."""

from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")

from quant_platform.rl_product.agent.network import ActorCriticModule, SplitTrunkActorCritic
from tests.platform.rl_product.g34.conftest import schema_from_config


def test_zero_context_ablation_ignores_context_block():
    schema = schema_from_config()
    core = SplitTrunkActorCritic(
        schema,
        price_trunk_hidden=(64, 32),
        context_trunk_hidden=(16, 8),
        portfolio_trunk_hidden=(16, 8),
    )
    model = ActorCriticModule(core)
    obs_dim = schema.obs_dim
    base = torch.randn(1, obs_dim)
    alt = base.clone()

    ctx = schema.block_slices()["context"]
    alt[:, ctx] = torch.randn(1, ctx.stop - ctx.start)

    act_base, _, _ = model.act(base, deterministic=True)
    act_alt, _, _ = model.act(alt, deterministic=True)
    assert not torch.allclose(act_base, act_alt)

    zero = base.clone()
    zero[:, ctx] = 0.0
    zero_alt = alt.clone()
    zero_alt[:, ctx] = 0.0
    act_zero, _, _ = model.act(zero, deterministic=True)
    act_zero_alt, _, _ = model.act(zero_alt, deterministic=True)
    assert torch.allclose(act_zero, act_zero_alt)


def test_zero_context_flag_matches_manual_zero():
    schema = schema_from_config()
    core = SplitTrunkActorCritic(
        schema,
        price_trunk_hidden=(32, 16),
        context_trunk_hidden=(8, 4),
        portfolio_trunk_hidden=(8, 4),
    )
    model = ActorCriticModule(core)
    obs = torch.randn(2, schema.obs_dim)
    ctx = schema.block_slices()["context"]
    manual = obs.clone()
    manual[:, ctx] = 0.0
    act_flag, _, _ = model.act(obs, deterministic=True, zero_context=True)
    act_manual, _, _ = model.act(manual, deterministic=True, zero_context=False)
    assert torch.allclose(act_flag, act_manual)
