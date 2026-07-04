"""G35 — reward normalizer."""

from __future__ import annotations

from quant_platform.rl_product.training.reward_norm import RewardNormalizer


def test_reward_normalizer_clips_to_sigma():
    norm = RewardNormalizer(clip_sigma=5.0, warmup_steps=0)
    for r in [0.0, 0.1, -0.1, 0.2, 0.05]:
        norm.update(r)
    clipped = norm.normalize(100.0, update=False)
    assert abs(clipped) <= 5.0


def test_reward_warmup_skips_stats():
    norm = RewardNormalizer(warmup_steps=3)
    norm.normalize(1.0)
    norm.normalize(2.0)
    norm.normalize(3.0)
    assert norm.count == 0
    norm.normalize(4.0)
    assert norm.count == 1
