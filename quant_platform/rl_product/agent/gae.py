"""GAE advantage estimation (G34)."""

from __future__ import annotations

from typing import Any


def compute_gae(
    rewards: Any,
    values: Any,
    dones: Any,
    *,
    gamma: float = 0.99,
    gae_lambda: float = 0.95,
) -> tuple[Any, Any]:
    """Generalized Advantage Estimation — returns (advantages, returns)."""
    import torch

    rewards_t = torch.as_tensor(rewards, dtype=torch.float32)
    values_t = torch.as_tensor(values, dtype=torch.float32)
    dones_t = torch.as_tensor(dones, dtype=torch.float32)

    if rewards_t.ndim == 0:
        rewards_t = rewards_t.unsqueeze(0)
        values_t = values_t.unsqueeze(0)
        dones_t = dones_t.unsqueeze(0)

    t_steps = rewards_t.shape[0]
    advantages = torch.zeros_like(rewards_t)
    gae = torch.tensor(0.0)
    next_value = torch.tensor(0.0)

    for step in reversed(range(t_steps)):
        mask = 1.0 - dones_t[step]
        delta = rewards_t[step] + gamma * next_value * mask - values_t[step]
        gae = delta + gamma * gae_lambda * mask * gae
        advantages[step] = gae
        next_value = values_t[step]

    returns = advantages + values_t
    return advantages, returns


def normalize_advantages(advantages: Any, *, eps: float = 1e-8) -> Any:
    import torch

    adv = torch.as_tensor(advantages, dtype=torch.float32)
    std = adv.std(unbiased=False)
    if std < eps:
        return adv - adv.mean()
    return (adv - adv.mean()) / (std + eps)
