"""Agent configuration for split-trunk PPO (G34)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class AgentConfig:
    price_trunk_hidden: tuple[int, ...] = (256, 128)
    context_trunk_hidden: tuple[int, ...] = (32, 16)
    portfolio_trunk_hidden: tuple[int, ...] = (32, 16)
    learning_rate: float = 3e-4
    clip_ratio: float = 0.2
    gamma: float = 0.99
    gae_lambda: float = 0.95
    value_coef: float = 0.5
    entropy_coef: float = 0.01
    entropy_coef_start: float = 0.01
    entropy_coef_end: float = 0.001
    entropy_coef_min: float = 0.0005
    max_grad_norm: float = 0.5
    ppo_epochs: int = 4
    action_dim: int = 1
    action_low: float = -1.0
    action_high: float = 1.0

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> AgentConfig:
        agent = config.get("agent", config)
        training = config.get("training", {})
        market = str(training.get("market", "futures"))
        action_low = 0.0 if market == "spot" else -1.0
        return cls(
            price_trunk_hidden=tuple(int(x) for x in agent.get("price_trunk_hidden", (256, 128))),
            context_trunk_hidden=tuple(int(x) for x in agent.get("context_trunk_hidden", (32, 16))),
            portfolio_trunk_hidden=tuple(int(x) for x in agent.get("portfolio_trunk_hidden", (32, 16))),
            learning_rate=float(agent.get("learning_rate", 3e-4)),
            clip_ratio=float(agent.get("clip_ratio", 0.2)),
            gamma=float(agent.get("gamma", 0.99)),
            gae_lambda=float(agent.get("gae_lambda", 0.95)),
            value_coef=float(agent.get("value_coef", 0.5)),
            entropy_coef=float(agent.get("entropy_coef", agent.get("entropy_coef_start", 0.01))),
            entropy_coef_start=float(agent.get("entropy_coef_start", 0.01)),
            entropy_coef_end=float(agent.get("entropy_coef_end", 0.001)),
            entropy_coef_min=float(agent.get("entropy_coef_min", 0.0005)),
            max_grad_norm=float(agent.get("max_grad_norm", 0.5)),
            ppo_epochs=int(agent.get("ppo_epochs", 4)),
            action_dim=int(agent.get("action_dim", 1)),
            action_low=float(agent.get("action_low", action_low)),
            action_high=float(agent.get("action_high", 1.0)),
        )
