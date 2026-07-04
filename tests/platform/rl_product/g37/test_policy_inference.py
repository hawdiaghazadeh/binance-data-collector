"""G37 — policy inference and graph hash parity."""

from __future__ import annotations

from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

from quant_platform.rl_product.agent.checkpoint import save_checkpoint
from quant_platform.rl_product.agent.ppo import PPOTrainer
from quant_platform.rl_product.graph import RLProductGraph
from quant_platform.rl_product.inference.policy_inference import GraphHashMismatchError, PolicyInferenceEngine
from quant_platform.rl_product.observation.schema import ObservationSchema
from quant_platform.rl_product.training.loop import OnlineTrainingLoop
from tests.platform.rl_product.g37.conftest import deploy_config, make_episode


def _train_and_save(tmp_path: Path) -> tuple[Path, dict]:
    config = deploy_config()
    episode = make_episode(30)
    loop = OnlineTrainingLoop.compile(config, [episode])
    loop.run(total_timesteps=16)
    ckpt = tmp_path / "policy.pt"
    schema = ObservationSchema.from_config(config)
    save_checkpoint(
        ckpt,
        loop._trainer.model,  # noqa: SLF001
        schema=schema,
        graph_schema_hash=loop.graph_schema_hash,
    )
    return ckpt, config


def test_policy_inference_loads_with_hash_parity(tmp_path: Path):
    ckpt, config = _train_and_save(tmp_path)
    engine = PolicyInferenceEngine.from_checkpoint(ckpt, config)
    assert engine.graph_schema_hash
    assert engine.metadata["graph_schema_hash"] == engine.graph_schema_hash
    obs = engine.build_observation(
        make_episode(20).bars,
        10,
        {"market": "spot", "initial_equity": 10_000.0, "equity": 10_000.0, "cash": 10_000.0, "position": 0.0},
    )
    action = engine.act(obs)
    assert isinstance(action, float)


def test_graph_hash_mismatch_rejected(tmp_path: Path):
    ckpt, config = _train_and_save(tmp_path)
    bad_config = deploy_config(perception={"master_gate": 0.0})
    with pytest.raises(GraphHashMismatchError):
        PolicyInferenceEngine.from_checkpoint(ckpt, bad_config)
