"""Online PPO training loop (G35)."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from quant_platform.rl_product.agent.checkpoint import save_checkpoint
from quant_platform.rl_product.agent.ppo import PPOTrainer
from quant_platform.rl_product.graph import RLProductGraph
from quant_platform.rl_product.observation.schema import ObservationSchema
from quant_platform.rl_product.protocols import Episode
from quant_platform.rl_product.training.curriculum import CurriculumScheduler
from quant_platform.rl_product.training.entropy_schedule import EntropySchedule
from quant_platform.rl_product.training.reward_norm import RewardNormalizer
from quant_platform.rl_product.training.rollout import AsyncRolloutCollector


@dataclass
class TrainingMetrics:
    timesteps: int = 0
    updates: int = 0
    episodes: int = 0
    last_loss: float = 0.0
    last_entropy: float = 0.0
    last_reward_mean: float = 0.0
    action_entropy_sum: float = 0.0
    trade_count_sum: int = 0
    history: list[dict[str, float]] = field(default_factory=list)


class OnlineTrainingLoop:
    """Frozen-graph training — no runtime plugin discovery in the loop."""

    __slots__ = (
        "_config",
        "_graph",
        "_trainer",
        "_episodes",
        "_reward_norm",
        "_entropy_schedule",
        "_collector",
        "_curriculum",
        "_schema",
        "_rollout_steps",
        "_checkpoint_dir",
    )

    def __init__(
        self,
        *,
        config: dict[str, Any],
        graph: RLProductGraph,
        trainer: PPOTrainer,
        episodes: list[Episode],
        reward_normalizer: RewardNormalizer | None = None,
        entropy_schedule: EntropySchedule | None = None,
        collector: AsyncRolloutCollector | None = None,
        curriculum: CurriculumScheduler | None = None,
        checkpoint_dir: str | Path | None = None,
    ) -> None:
        self._config = config
        self._graph = graph
        self._trainer = trainer
        self._episodes = episodes
        self._schema = ObservationSchema.from_config(config)
        self._reward_norm = reward_normalizer or RewardNormalizer.from_config(config)
        self._entropy_schedule = entropy_schedule or EntropySchedule.from_config(config)
        self._collector = collector or AsyncRolloutCollector()
        self._curriculum = curriculum or CurriculumScheduler.from_config(config)
        training = config.get("training", config)
        self._rollout_steps = int(training.get("rollout_steps", 128))
        self._checkpoint_dir = Path(checkpoint_dir) if checkpoint_dir else None

    @classmethod
    def compile(
        cls,
        config: dict[str, Any],
        episodes: list[Episode],
        *,
        trainer: PPOTrainer | None = None,
        checkpoint_dir: str | Path | None = None,
    ) -> OnlineTrainingLoop:
        graph = RLProductGraph.compile(config)
        if trainer is None:
            trainer = PPOTrainer.from_schema(ObservationSchema.from_config(config), config)
        return cls(
            config=config,
            graph=graph,
            trainer=trainer,
            episodes=episodes,
            checkpoint_dir=checkpoint_dir,
        )

    @property
    def graph(self) -> RLProductGraph:
        return self._graph

    @property
    def graph_schema_hash(self) -> str:
        return self._graph.schema_hash

    def _select_episodes(self) -> list[Episode]:
        pool = self._curriculum.filter_episodes(self._episodes)
        return pool if pool else self._episodes

    def run(self, *, total_timesteps: int | None = None) -> TrainingMetrics:
        agent = self._config.get("agent", self._config)
        training = self._config.get("training", self._config)
        target = total_timesteps or int(agent.get("total_timesteps", training.get("total_timesteps", 256)))
        metrics = TrainingMetrics()
        self._reward_norm.reset()
        episode_ids = {ep.episode_id: ep for ep in self._episodes}
        rng = random.Random(int(training.get("seed", 42)))

        while metrics.timesteps < target:
            pool = self._select_episodes()
            episode = rng.choice(pool)
            next_ids = [ep_id for ep_id in episode_ids if ep_id != episode.episode_id][:2]

            self._trainer.set_entropy_coef(self._entropy_schedule.coef_at(metrics.timesteps))
            batch = self._collector.collect_episode(
                episode,
                self._trainer,
                self._graph,
                n_steps=min(self._rollout_steps, target - metrics.timesteps),
                reward_normalizer=self._reward_norm,
                prefetch_ids=next_ids,
                episode_loader=lambda ep_id: episode_ids[ep_id],
            )
            update_metrics = self._trainer.update(batch)
            metrics.timesteps += batch.batch_size
            metrics.updates += 1
            metrics.episodes += 1
            metrics.last_loss = update_metrics.get("loss", 0.0)
            metrics.last_entropy = update_metrics.get("entropy", 0.0)
            metrics.last_reward_mean = sum(batch.rewards) / max(len(batch.rewards), 1)
            metrics.action_entropy_sum += metrics.last_entropy
            metrics.history.append(
                {
                    "loss": metrics.last_loss,
                    "entropy": metrics.last_entropy,
                    "reward_mean": metrics.last_reward_mean,
                    "timesteps": float(metrics.timesteps),
                }
            )
            self._curriculum.advance(batch.batch_size)

            if self._checkpoint_dir and metrics.updates % int(training.get("checkpoint_every", 10)) == 0:
                self._checkpoint_dir.mkdir(parents=True, exist_ok=True)
                path = self._checkpoint_dir / f"checkpoint_{metrics.timesteps}.pt"
                save_checkpoint(
                    path,
                    self._trainer.model,
                    schema=self._schema,
                    graph_schema_hash=self._graph.schema_hash,
                )

        return metrics
