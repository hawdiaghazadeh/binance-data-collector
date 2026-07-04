"""Policy rollout evaluation on episodes (G36)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from quant_platform.rl_product.agent.ppo import PPOTrainer
from quant_platform.rl_product.env.bridge import RLEnvironmentBridge
from quant_platform.rl_product.evaluation.metrics import EvalMetrics, summarize_equity_curve
from quant_platform.rl_product.graph import RLProductGraph
from quant_platform.rl_product.protocols import Episode


@dataclass(frozen=True, slots=True)
class EvalOptions:
    zero_context: bool = False
    zero_price: bool = False
    deterministic: bool = True


class PolicyEvaluator:
    """Run a trained policy through episodes and compute OOS metrics."""

    def evaluate_episodes(
        self,
        trainer: PPOTrainer,
        graph: RLProductGraph,
        episodes: list[Episode],
        *,
        options: EvalOptions | None = None,
    ) -> EvalMetrics:
        opts = options or EvalOptions()
        if not episodes:
            return EvalMetrics()
        per_episode = [
            self.evaluate_episode(trainer, graph, episode, options=opts) for episode in episodes
        ]
        equity_curve: list[float] = []
        trade_count = 0
        for result in per_episode:
            if equity_curve:
                offset = result.equity_curve[0]
                scale = equity_curve[-1] / offset if offset > 0 else 1.0
                equity_curve.extend(value * scale for value in result.equity_curve[1:])
            else:
                equity_curve.extend(result.equity_curve)
            trade_count += result.trade_count
        return summarize_equity_curve(equity_curve, trade_count=trade_count)

    def evaluate_episode(
        self,
        trainer: PPOTrainer,
        graph: RLProductGraph,
        episode: Episode,
        *,
        options: EvalOptions | None = None,
    ) -> EvalMetrics:
        import torch

        opts = options or EvalOptions()
        training = graph.config.get("training", graph.config)
        env = RLEnvironmentBridge(
            episode,
            graph,
            market=str(training.get("market", "futures")),
            initial_equity=float(training.get("initial_equity", 10_000.0)),
            leverage=float(training.get("leverage", 5.0)),
            config=graph.config,
        )
        obs, _ = env.reset()
        price = episode.bars[0].close
        equity_curve = [env.portfolio.equity(price)]
        done = False

        while not done:
            obs_tensor = torch.as_tensor(obs, dtype=torch.float32).unsqueeze(0)
            action, _, _ = trainer.model.act(
                obs_tensor,
                deterministic=opts.deterministic,
                zero_context=opts.zero_context,
                zero_price=opts.zero_price,
            )
            action_val = float(action.squeeze().detach())
            obs, _reward, done, _info = env.step(action_val)
            bar = episode.bars[min(env.cursor.t, len(episode.bars) - 1)]
            equity_curve.append(env.portfolio.equity(bar.close))

        return summarize_equity_curve(equity_curve, trade_count=env.portfolio.trade_count)

    def action_entropy_mean(
        self,
        trainer: PPOTrainer,
        graph: RLProductGraph,
        episodes: list[Episode],
        *,
        options: EvalOptions | None = None,
    ) -> float:
        import torch

        opts = options or EvalOptions()
        entropies: list[float] = []
        for episode in episodes:
            training = graph.config.get("training", graph.config)
            env = RLEnvironmentBridge(
                episode,
                graph,
                market=str(training.get("market", "futures")),
                initial_equity=float(training.get("initial_equity", 10_000.0)),
                leverage=float(training.get("leverage", 5.0)),
                config=graph.config,
            )
            obs, _ = env.reset()
            done = False
            while not done:
                obs_tensor = torch.as_tensor(obs, dtype=torch.float32).unsqueeze(0)
                _action, _log_prob, _value = trainer.model.act(
                    obs_tensor,
                    deterministic=False,
                    zero_context=opts.zero_context,
                    zero_price=opts.zero_price,
                )
                _new_log_prob, _value, entropy = trainer.model.evaluate_actions(
                    obs_tensor,
                    _action,
                    zero_context=opts.zero_context,
                    zero_price=opts.zero_price,
                )
                entropies.append(float(entropy.mean().detach()))
                obs, _reward, done, _info = env.step(float(_action.squeeze().detach()))
        return sum(entropies) / len(entropies) if entropies else 0.0
