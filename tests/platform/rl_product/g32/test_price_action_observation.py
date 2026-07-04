"""G32 — price-action observation builder."""

from __future__ import annotations

import array

import pytest

from quant_platform.rl_product.observation.builder import PriceActionObservationBuilder
from quant_platform.rl_product.observation.schema import ObservationSchema
from tests.platform.rl_product.g32.conftest import trending_bars


def test_build_observation_dim_and_dtype():
    bars = trending_bars(80)
    builder = PriceActionObservationBuilder(ObservationSchema())
    obs = builder.build(bars, 79, portfolio={"equity": 10000, "initial_equity": 10000})
    assert len(obs.data) == 128
    assert obs.data.typecode == "f"
    assert isinstance(obs.data, array.array)
    assert obs.schema.schema_version == "1.0"


def test_price_block_nonzero_with_data():
    bars = trending_bars(80)
    builder = PriceActionObservationBuilder(ObservationSchema())
    obs = builder.build(bars, 79)
    price = obs.block("price_action")
    assert any(abs(v) > 0 for v in price)


def test_master_gate_zeros_context_block():
    bars = trending_bars(80)
    config = {
        "observation": {"dim": 128, "context_dims": 16},
        "perception": {"master_gate": 0.0},
    }
    builder = PriceActionObservationBuilder.from_config(config)
    obs = builder.build(bars, 79, config=config)
    context = obs.block("context")
    assert len(context) == 16
    assert all(v == 0.0 for v in context)


def test_full_context_with_master_gate_one():
    bars = trending_bars(80)
    config = {
        "observation": {"dim": 128, "context_dims": 16},
        "perception": {"master_gate": 1.0},
    }
    builder = PriceActionObservationBuilder.from_config(config)
    obs = builder.build(bars, 79, config=config)
    context = obs.block("context")
    assert any(abs(v) > 0 for v in context)


def test_no_lookahead_observation():
    bars = trending_bars(60)
    builder = PriceActionObservationBuilder(ObservationSchema())
    t = 40
    obs_a = builder.build(bars, t)
    extended = bars + [trending_bars(1)[0]]
    obs_b = builder.build(extended, t)
    assert obs_a.block("price_action") == obs_b.block("price_action")
    assert obs_a.block("context") == obs_b.block("context")


def test_context_dims_32():
    schema = ObservationSchema(obs_dim=256, context_dims=32, portfolio_dims=14, reserved_dims=8)
    schema.validate_budget()
    assert schema.price_dims == 202
    bars = trending_bars(80)
    builder = PriceActionObservationBuilder(schema)
    obs = builder.build(
        bars,
        79,
        config={"observation": {"dim": 256, "context_dims": 32}},
    )
    assert len(obs.block("context")) == 32
    assert len(obs.data) == 256
