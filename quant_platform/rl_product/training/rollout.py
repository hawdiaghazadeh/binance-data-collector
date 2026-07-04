"""Rollout collection — sync env loop with optional async episode prefetch (G35)."""

from __future__ import annotations

from typing import Any, Callable

from quant_platform.rl_product.agent.buffer import RolloutBatch
from quant_platform.rl_product.agent.ppo import PPOTrainer
from quant_platform.rl_product.dataset.cache import EpisodeCache
from quant_platform.rl_product.env.bridge import RLEnvironmentBridge
from quant_platform.rl_product.graph import RLProductGraph
from quant_platform.rl_product.protocols import Episode
from quant_platform.rl_product.training.reward_norm import RewardNormalizer


class RolloutCollector:
    """Collect fixed-length rollout tensors from an environment bridge."""

    def collect(
        self,
        env: RLEnvironmentBridge,
        trainer: PPOTrainer,
        *,
        n_steps: int,
        reward_normalizer: RewardNormalizer | None = None,
    ) -> RolloutBatch:
        import torch

        observations: list[list[float]] = []
        actions: list[list[float]] = []
        log_probs: list[float] = []
        rewards: list[float] = []
        values: list[float] = []
        dones: list[float] = []

        obs, _ = env.reset()
        done = False
        steps = 0

        while steps < n_steps:
            obs_tensor = torch.as_tensor(obs, dtype=torch.float32).unsqueeze(0)
            action, log_prob, value = trainer.model.act(obs_tensor)
            action_val = float(action.squeeze().detach())
            next_obs, reward, done, _info = env.step(action_val)
            if reward_normalizer is not None:
                reward = reward_normalizer.normalize(reward)

            observations.append(list(obs))
            actions.append([action_val])
            log_probs.append(float(log_prob.squeeze().detach()))
            rewards.append(float(reward))
            values.append(float(value.squeeze().detach()))
            dones.append(1.0 if done else 0.0)
            steps += 1
            obs = next_obs
            if done:
                obs, _ = env.reset()
                done = False

        return RolloutBatch(
            observations=observations,
            actions=actions,
            log_probs=log_probs,
            rewards=rewards,
            values=values,
            dones=dones,
        )


class AsyncRolloutCollector(RolloutCollector):
    """Episode-cache prefetch while collecting rollouts."""

    __slots__ = ("_cache", "_bridge_kwargs")

    def __init__(
        self,
        *,
        episode_cache: EpisodeCache | None = None,
        bridge_kwargs: dict[str, Any] | None = None,
    ) -> None:
        self._cache = episode_cache or EpisodeCache()
        self._bridge_kwargs = bridge_kwargs or {}

    @property
    def episode_cache(self) -> EpisodeCache:
        return self._cache

    def make_env(self, episode: Episode, graph: RLProductGraph) -> RLEnvironmentBridge:
        training = graph.config.get("training", graph.config)
        market = str(training.get("market", "futures"))
        initial_equity = float(training.get("initial_equity", 10_000.0))
        leverage = float(training.get("leverage", 5.0))
        kwargs = dict(self._bridge_kwargs)
        return RLEnvironmentBridge(
            episode,
            graph,
            market=market,
            initial_equity=initial_equity,
            leverage=leverage,
            config=graph.config,
            **kwargs,
        )

    def collect_episode(
        self,
        episode: Episode,
        trainer: PPOTrainer,
        graph: RLProductGraph,
        *,
        n_steps: int,
        reward_normalizer: RewardNormalizer | None = None,
        prefetch_ids: list[str] | None = None,
        episode_loader: Callable[[str], Episode] | None = None,
    ) -> RolloutBatch:
        if prefetch_ids and episode_loader is not None:
            self._cache.prefetch(prefetch_ids, episode_loader)

        ep = self._cache.get(episode.episode_id, lambda: episode)
        env = self.make_env(ep, graph)
        return self.collect(env, trainer, n_steps=n_steps, reward_normalizer=reward_normalizer)
