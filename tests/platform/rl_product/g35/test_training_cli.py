"""G35 — quant-train CLI and plugin registration."""

from __future__ import annotations
import json
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
yaml = pytest.importorskip("yaml")

from quant_platform.core.manager import PluginManager
from quant_platform.core.registry import BaseRegistry
from quant_platform.plugins.rl import RL_PLUGINS
from quant_platform.rl_product.pipeline import register_rl_product_plugins
from quant_platform.rl_product.registry import RL_GROUP
from quant_platform.rl_product.training.cli import main as train_main
from tests.platform.rl_product.g35.conftest import train_config


@pytest.fixture(autouse=True)
def _clean_rl_registry():
    reg = BaseRegistry.get_instance(RL_GROUP)
    for meta in reg.list_plugins():
        reg.unregister(meta.name)
    yield


def test_g35_plugins_registered():
    manager = PluginManager()
    register_rl_product_plugins(manager)
    names = {meta.name for meta, _ in RL_PLUGINS}
    assert "online_training" in names
    assert "curriculum_scheduler" in names


def test_quant_train_cli_smoke(tmp_path: Path, capsys):
    config = train_config()
    config["training"]["total_timesteps"] = 16
    config["training"]["rollout_steps"] = 8
    cfg_path = tmp_path / "train.yaml"
    cfg_path.write_text(yaml.dump(config), encoding="utf-8")
    code = train_main(["train", "--config", str(cfg_path), "--steps", "16", "--checkpoint-dir", str(tmp_path / "ckpt")])
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["timesteps"] >= 16
    assert "graph_schema_hash" in out
