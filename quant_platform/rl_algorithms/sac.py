"""SAC algorithm skeleton (Phase 15)."""

from __future__ import annotations

from typing import Any

from quant_platform.rl_algorithms.source import batch_rewards


def sac_train_step(
    batch: list[Any],
    *,
    learning_rate: float = 3e-4,
    entropy_coef: float = 0.2,
    critic_coef: float = 0.5,
) -> dict[str, float | int]:
    if not batch:
        return {
            "loss": 0.0,
            "batch_size": 0,
            "actor_loss": 0.0,
            "critic_loss": 0.0,
            "entropy": entropy_coef,
        }

    rewards = batch_rewards(batch)
    mean_reward = sum(rewards) / len(rewards) if rewards else 0.0
    actor_loss = -mean_reward * learning_rate
    critic_loss = abs(mean_reward) * critic_coef * learning_rate
    entropy_bonus = entropy_coef * learning_rate
    total_loss = actor_loss + critic_loss - entropy_bonus

    return {
        "loss": total_loss,
        "batch_size": len(batch),
        "actor_loss": actor_loss,
        "critic_loss": critic_loss,
        "entropy": entropy_coef,
        "mean_reward": mean_reward,
    }
