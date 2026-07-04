"""RL evaluation metrics (G36)."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from quant_platform.rewards.sharpe import compute_sharpe_ratio


@dataclass(slots=True)
class EvalMetrics:
    sharpe: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    trade_count: int = 0
    total_return: float = 0.0
    steps: int = 0
    step_returns: list[float] = field(default_factory=list)
    equity_curve: list[float] = field(default_factory=list)

    def to_dict(self) -> dict[str, float | int | list[float]]:
        return {
            "sharpe": self.sharpe,
            "max_drawdown": self.max_drawdown,
            "win_rate": self.win_rate,
            "trade_count": self.trade_count,
            "total_return": self.total_return,
            "steps": self.steps,
            "step_returns": list(self.step_returns),
            "equity_curve": list(self.equity_curve),
        }


def equity_step_returns(equity_curve: list[float]) -> list[float]:
    if len(equity_curve) < 2:
        return []
    returns: list[float] = []
    for prev, current in zip(equity_curve, equity_curve[1:], strict=False):
        if abs(prev) < 1e-12:
            returns.append(0.0)
        else:
            returns.append((current - prev) / prev)
    return returns


def compute_max_drawdown(equity_curve: list[float]) -> float:
    if not equity_curve:
        return 0.0
    peak = equity_curve[0]
    max_dd = 0.0
    for equity in equity_curve:
        peak = max(peak, equity)
        if peak > 0:
            max_dd = max(max_dd, (peak - equity) / peak)
    return max_dd


def compute_win_rate(step_returns: list[float]) -> float:
    if not step_returns:
        return 0.0
    wins = sum(1 for value in step_returns if value > 0)
    return wins / len(step_returns)


def summarize_equity_curve(
    equity_curve: list[float],
    *,
    trade_count: int = 0,
) -> EvalMetrics:
    step_returns = equity_step_returns(equity_curve)
    initial = equity_curve[0] if equity_curve else 0.0
    final = equity_curve[-1] if equity_curve else 0.0
    total_return = (final - initial) / initial if initial > 0 else 0.0
    return EvalMetrics(
        sharpe=compute_sharpe_ratio(step_returns),
        max_drawdown=compute_max_drawdown(equity_curve),
        win_rate=compute_win_rate(step_returns),
        trade_count=trade_count,
        total_return=total_return,
        steps=max(len(equity_curve) - 1, 0),
        step_returns=step_returns,
        equity_curve=list(equity_curve),
    )


def aggregate_metrics(metrics: list[EvalMetrics]) -> EvalMetrics:
    if not metrics:
        return EvalMetrics()
    sharpe = sum(m.sharpe for m in metrics) / len(metrics)
    max_dd = max(m.max_drawdown for m in metrics)
    win_rate = sum(m.win_rate for m in metrics) / len(metrics)
    trade_count = sum(m.trade_count for m in metrics)
    total_return = sum(m.total_return for m in metrics) / len(metrics)
    steps = sum(m.steps for m in metrics)
    return EvalMetrics(
        sharpe=sharpe,
        max_drawdown=max_dd,
        win_rate=win_rate,
        trade_count=trade_count,
        total_return=total_return,
        steps=steps,
    )
