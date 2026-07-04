"""Walk-forward RL evaluation (G36)."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from quant_platform.rl_product.agent.ppo import PPOTrainer
from quant_platform.rl_product.evaluation.evaluator import EvalOptions, PolicyEvaluator
from quant_platform.rl_product.evaluation.metrics import EvalMetrics, aggregate_metrics
from quant_platform.rl_product.graph import RLProductGraph
from quant_platform.rl_product.protocols import Episode
from quant_platform.rl_product.training.loop import OnlineTrainingLoop
from quant_platform.rl_product.training.reward_norm import RewardNormalizer


@dataclass(frozen=True, slots=True)
class WalkForwardConfig:
    folds: int = 4
    train_timesteps: int = 64
    min_folds: int = 4

    @classmethod
    def from_config(cls, config: dict) -> WalkForwardConfig:
        evaluation = config.get("evaluation", config)
        return cls(
            folds=int(evaluation.get("walk_forward_folds", evaluation.get("folds", 4))),
            train_timesteps=int(
                evaluation.get(
                    "train_timesteps",
                    config.get("training", {}).get("total_timesteps", 64),
                )
            ),
            min_folds=int(evaluation.get("min_folds", 4)),
        )


def build_episode_folds(
    episodes: list[Episode],
    *,
    n_folds: int,
) -> list[tuple[list[Episode], list[Episode]]]:
    ordered = sorted(episodes, key=lambda ep: (ep.start_idx, ep.episode_id))
    n = len(ordered)
    if n < 2:
        raise ValueError("need at least 2 episodes for walk-forward evaluation")
    chunk = max(1, n // (n_folds + 1))
    folds: list[tuple[list[Episode], list[Episode]]] = []
    for i in range(n_folds):
        test_start = (i + 1) * chunk
        test_end = min(test_start + chunk, n)
        if test_start >= n:
            break
        train = ordered[:test_start]
        test = ordered[test_start:test_end]
        if train and test:
            folds.append((train, test))
    if not folds:
        split = max(1, n // 2)
        folds.append((ordered[:split], ordered[split:]))
    return folds


class WalkForwardRLEvaluator:
    """Expanding-window walk-forward over RL episodes."""

    def __init__(
        self,
        *,
        evaluator: PolicyEvaluator | None = None,
        wf_config: WalkForwardConfig | None = None,
    ) -> None:
        self._evaluator = evaluator or PolicyEvaluator()
        self._wf_config = wf_config

    def evaluate(
        self,
        config: dict[str, Any],
        episodes: list[Episode],
        *,
        trainer: PPOTrainer | None = None,
    ) -> dict[str, Any]:
        wf = self._wf_config or WalkForwardConfig.from_config(config)
        folds = build_episode_folds(episodes, n_folds=wf.folds)
        if len(folds) < wf.min_folds:
            raise ValueError(f"walk-forward requires >= {wf.min_folds} folds, got {len(folds)}")

        fold_results: list[dict[str, Any]] = []
        oos_metrics: list[EvalMetrics] = []

        for index, (train_eps, test_eps) in enumerate(folds):
            fold_config = copy.deepcopy(config)
            fold_config.setdefault("training", {})["total_timesteps"] = wf.train_timesteps
            RewardNormalizer.from_config(fold_config).reset()

            if trainer is None:
                loop = OnlineTrainingLoop.compile(fold_config, train_eps)
                loop.run(total_timesteps=wf.train_timesteps)
                fold_trainer = loop._trainer  # noqa: SLF001 — eval uses trained policy
                graph = loop.graph
            else:
                loop = OnlineTrainingLoop.compile(fold_config, train_eps, trainer=trainer)
                loop.run(total_timesteps=wf.train_timesteps)
                fold_trainer = trainer
                graph = loop.graph

            metrics = self._evaluator.evaluate_episodes(fold_trainer, graph, test_eps)
            oos_metrics.append(metrics)
            fold_results.append(
                {
                    "fold": index,
                    "train_episodes": len(train_eps),
                    "test_episodes": len(test_eps),
                    "oos_sharpe": metrics.sharpe,
                    "oos_max_drawdown": metrics.max_drawdown,
                    "oos_win_rate": metrics.win_rate,
                    "trade_count": metrics.trade_count,
                }
            )

        aggregate = aggregate_metrics(oos_metrics)
        return {
            "method": "walk_forward_rl",
            "folds": len(fold_results),
            "fold_results": fold_results,
            "oos_sharpe_mean": aggregate.sharpe,
            "oos_max_drawdown": aggregate.max_drawdown,
            "oos_win_rate_mean": aggregate.win_rate,
            "graph_schema_hash": RLProductGraph.compile(config).schema_hash,
        }
