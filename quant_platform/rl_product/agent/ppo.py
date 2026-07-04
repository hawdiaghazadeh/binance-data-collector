"""PPO trainer — clipped surrogate with grad clip (G34)."""

from __future__ import annotations

from typing import Any

from quant_platform.rl_product.agent.buffer import RolloutBatch
from quant_platform.rl_product.agent.config import AgentConfig
from quant_platform.rl_product.agent.gae import compute_gae, normalize_advantages
from quant_platform.rl_product.agent.network import ActorCriticModule, SplitTrunkActorCritic


class PPOTrainer:
    """Production-safe PPO update with mandatory advantage normalization."""

    __slots__ = ("_model", "_config", "_optimizer")

    def __init__(self, model: ActorCriticModule, config: AgentConfig) -> None:
        import torch

        self._model = model
        self._config = config
        self._optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)

    @classmethod
    def from_schema(cls, schema, config: dict[str, Any]) -> PPOTrainer:
        agent_cfg = AgentConfig.from_config(config)
        core = SplitTrunkActorCritic(
            schema,
            price_trunk_hidden=agent_cfg.price_trunk_hidden,
            context_trunk_hidden=agent_cfg.context_trunk_hidden,
            portfolio_trunk_hidden=agent_cfg.portfolio_trunk_hidden,
            action_dim=agent_cfg.action_dim,
        )
        return cls(ActorCriticModule(core), agent_cfg)

    @property
    def model(self) -> ActorCriticModule:
        return self._model

    @property
    def config(self) -> AgentConfig:
        return self._config

    def compute_advantages(self, batch: RolloutBatch) -> RolloutBatch:
        advantages, returns = compute_gae(
            batch.rewards,
            batch.values,
            batch.dones,
            gamma=self._config.gamma,
            gae_lambda=self._config.gae_lambda,
        )
        batch.advantages = normalize_advantages(advantages)
        batch.returns = returns
        return batch

    def update(self, batch: RolloutBatch, *, zero_context: bool = False) -> dict[str, float]:
        import torch

        cfg = self._config
        if batch.advantages is None or batch.returns is None:
            batch = self.compute_advantages(batch)

        obs = torch.as_tensor(batch.observations, dtype=torch.float32)
        actions = torch.as_tensor(batch.actions, dtype=torch.float32)
        old_log_probs = torch.as_tensor(batch.log_probs, dtype=torch.float32)
        advantages = torch.as_tensor(batch.advantages, dtype=torch.float32)
        returns = torch.as_tensor(batch.returns, dtype=torch.float32)

        if actions.ndim == 1:
            actions = actions.unsqueeze(-1)

        metrics: dict[str, float] = {}
        for _ in range(cfg.ppo_epochs):
            new_log_probs, values, entropy = self._model.evaluate_actions(
                obs, actions, zero_context=zero_context
            )
            ratio = torch.exp(new_log_probs - old_log_probs)
            surr1 = ratio * advantages
            surr2 = torch.clamp(ratio, 1.0 - cfg.clip_ratio, 1.0 + cfg.clip_ratio) * advantages
            policy_loss = -torch.min(surr1, surr2).mean()
            value_loss = cfg.value_coef * (returns - values).pow(2).mean()
            entropy_loss = -cfg.entropy_coef * entropy.mean()
            loss = policy_loss + value_loss + entropy_loss

            self._optimizer.zero_grad()
            loss.backward()
            grad_norm = torch.nn.utils.clip_grad_norm_(list(self._model.parameters()), cfg.max_grad_norm)
            self._optimizer.step()

            metrics = {
                "loss": float(loss.detach()),
                "policy_loss": float(policy_loss.detach()),
                "value_loss": float(value_loss.detach()),
                "entropy": float(entropy.mean().detach()),
                "grad_norm": float(grad_norm),
            }

        return metrics
