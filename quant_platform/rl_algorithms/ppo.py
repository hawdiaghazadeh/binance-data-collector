"""PPO algorithm skeleton (Phase 15)."""

from __future__ import annotations

from typing import Any

from quant_platform.rl_algorithms.source import batch_rewards


def ppo_train_step(
    batch: list[Any],
    *,
    clip_ratio: float = 0.2,
    learning_rate: float = 3e-4,
    value_coef: float = 0.5,
) -> dict[str, float | int]:
    if not batch:
        return {
            "loss": 0.0,
            "batch_size": 0,
            "policy_loss": 0.0,
            "value_loss": 0.0,
            "clip_ratio": clip_ratio,
        }

    rewards = batch_rewards(batch)
    mean_reward = sum(rewards) / len(rewards) if rewards else 0.0
    clipped = max(min(mean_reward, clip_ratio), -clip_ratio)
    policy_loss = -clipped * learning_rate
    value_loss = abs(mean_reward) * value_coef * learning_rate
    total_loss = policy_loss + value_loss

    return {
        "loss": total_loss,
        "batch_size": len(batch),
        "policy_loss": policy_loss,
        "value_loss": value_loss,
        "clip_ratio": clip_ratio,
        "mean_reward": mean_reward,
    }
