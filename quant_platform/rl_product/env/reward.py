"""Reward engine — PnL primary, risk secondary, capped context (G33)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from quant_platform.rl_product.env.portfolio import PortfolioTracker

MAX_CONTEXT_REWARD_ABS = 0.08


@dataclass(frozen=True, slots=True)
class RewardConfig:
    drawdown_penalty_weight: float = 0.15
    sharpe_component_weight: float = 0.10
    max_context_reward_weight: float = 0.05
    hint_conf_threshold: float = 0.5
    context_gate: bool = True

    def __post_init__(self) -> None:
        if self.max_context_reward_weight > MAX_CONTEXT_REWARD_ABS:
            raise ValueError(f"max_context_reward_weight must be <= {MAX_CONTEXT_REWARD_ABS}")

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> RewardConfig:
        reward = config.get("reward", config)
        perception = config.get("perception", {})
        max_ctx = float(reward.get("max_context_reward_weight", 0.05))
        master_gate = float(perception.get("master_gate", 1.0))
        return cls(
            drawdown_penalty_weight=float(reward.get("drawdown_penalty_weight", 0.15)),
            sharpe_component_weight=float(reward.get("sharpe_component_weight", 0.10)),
            max_context_reward_weight=max_ctx,
            hint_conf_threshold=float(reward.get("hint_conf_threshold", 0.5)),
            context_gate=master_gate > 0.0 and max_ctx > 0.0,
        )


class RewardEngine:
    __slots__ = ("_config",)

    def __init__(self, config: RewardConfig | None = None) -> None:
        self._config = config or RewardConfig()

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> RewardEngine:
        return cls(RewardConfig.from_config(config))

    @property
    def config(self) -> RewardConfig:
        return self._config

    def compute(
        self,
        *,
        step_pnl: float,
        portfolio: PortfolioTracker,
        hint_conf: float = 0.0,
    ) -> tuple[float, dict[str, float]]:
        cfg = self._config
        r_pnl = step_pnl / portfolio.initial_equity
        drawdown_pen = portfolio.drawdown * cfg.drawdown_penalty_weight
        sharpe_component = 0.0
        if step_pnl > 0 and portfolio.initial_equity > 0:
            sharpe_component = (step_pnl / portfolio.initial_equity) * cfg.sharpe_component_weight
        r_risk = -drawdown_pen + sharpe_component

        r_ctx = 0.0
        if (
            cfg.context_gate
            and cfg.max_context_reward_weight > 0.0
            and step_pnl > 0.0
            and hint_conf >= cfg.hint_conf_threshold
        ):
            r_ctx = min(cfg.max_context_reward_weight, hint_conf * cfg.max_context_reward_weight)

        total = r_pnl + r_risk + r_ctx
        components = {"pnl": r_pnl, "risk": r_risk, "context": r_ctx, "total": total}
        return total, components
