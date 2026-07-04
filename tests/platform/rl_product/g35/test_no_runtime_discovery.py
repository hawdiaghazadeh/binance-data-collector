"""G35 — frozen graph; no runtime plugin discovery in training loop."""

from __future__ import annotations
from unittest.mock import patch

import pytest

torch = pytest.importorskip("torch")

from quant_platform.rl_product.training.loop import OnlineTrainingLoop
from tests.platform.rl_product.g35.conftest import make_episode, train_config


def test_training_loop_does_not_discover_plugins():
    episodes = [make_episode()]
    config = train_config()
    with patch("quant_platform.core.manager.PluginManager.discover") as discover:
        loop = OnlineTrainingLoop.compile(config, episodes)
        loop.run(total_timesteps=16)
        discover.assert_not_called()
