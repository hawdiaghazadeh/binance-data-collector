"""G37 — PolicyStrategy on_bar hook."""

from __future__ import annotations

from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.plugins.rl.policy_strategy import factory as policy_strategy_factory
from quant_platform.rl_product.inference.strategy import action_to_signal
from tests.platform.rl_product.g37.conftest import deploy_config, make_kline_rows
from tests.platform.rl_product.g37.test_policy_inference import _train_and_save


def test_action_to_signal_spot():
    signal = action_to_signal(0.6, market="spot")
    assert signal["side"] == "buy"
    assert signal["size"] == pytest.approx(0.6)


def test_policy_strategy_on_bar(tmp_path: Path):
    ckpt, config = _train_and_save(tmp_path)
    strategy = policy_strategy_factory(checkpoint_path=ckpt, config=config)
    ctx = PipelineContext()
    ctx.emit(DataEnvelope(type_key="klines", payload=make_kline_rows(30)))
    strategy.on_bar(ctx)
    signals = strategy.signals(ctx)
    assert signals
    assert "side" in signals[0]
    assert signals[0]["graph_schema_hash"]
