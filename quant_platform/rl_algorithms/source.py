"""RL algorithm batch helpers (Phase 15)."""

from __future__ import annotations

from typing import Any


def batch_rewards(batch: list[Any]) -> list[float]:
    rewards: list[float] = []
    for item in batch:
        if isinstance(item, dict) and "reward" in item:
            rewards.append(float(item["reward"]))
    return rewards
