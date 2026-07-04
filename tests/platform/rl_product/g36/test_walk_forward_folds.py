"""G36 — walk-forward fold builder."""

from __future__ import annotations

from quant_platform.rl_product.evaluation.walk_forward import build_episode_folds
from tests.platform.rl_product.g36.conftest import make_episode_set


def test_build_episode_folds_min_four():
    episodes = make_episode_set(8)
    folds = build_episode_folds(episodes, n_folds=4)
    assert len(folds) >= 4
    for train, test in folds:
        assert train
        assert test
        assert all(ep.start_idx <= test[0].start_idx for ep in train)
