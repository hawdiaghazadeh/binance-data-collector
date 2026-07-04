"""G32 — observation schema budget validation."""

from __future__ import annotations

import pytest

from quant_platform.rl_product.observation.schema import ObservationSchema


def test_default_schema_passes_budget():
    schema = ObservationSchema()
    schema.validate_budget()
    assert schema.price_dims == 90
    assert schema.price_dims >= int(0.70 * schema.obs_dim)


def test_price_dims_below_minimum_raises():
    schema = ObservationSchema(obs_dim=128, context_dims=16, portfolio_dims=30, reserved_dims=8)
    with pytest.raises(ValueError, match="price_dims"):
        schema.validate_budget()


def test_context_dims_exceeds_25pct_raises():
    schema = ObservationSchema(obs_dim=80, context_dims=21, portfolio_dims=14, reserved_dims=8)
    with pytest.raises(ValueError, match="25%"):
        schema.validate_budget()


def test_context_dims_max_raises():
    schema = ObservationSchema(context_dims=33)
    with pytest.raises(ValueError, match="context_dims must be in"):
        schema.validate_budget()


def test_block_slices_cover_full_vector():
    schema = ObservationSchema()
    slices = schema.block_slices()
    assert slices["price_action"].stop - slices["price_action"].start == 90
    assert slices["context"].stop - slices["context"].start == 16
    assert slices["portfolio"].stop - slices["portfolio"].start == 14
    assert slices["reserved"].stop - slices["reserved"].start == 8
    assert slices["reserved"].stop == 128
