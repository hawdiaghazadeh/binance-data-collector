"""Vectorized backtest engine (Phase 17)."""

from __future__ import annotations

from typing import Any

from quant_platform.backtesting.source import closes_from_data, normalize_bars, pct_returns
from quant_platform.rewards.drawdown import compute_max_drawdown


def _resolve_positions(strategy: Any, bars: list[Any], closes: list[float]) -> list[float]:
    if hasattr(strategy, "positions"):
        weights = strategy.positions(bars)
        if isinstance(weights, list) and len(weights) == len(closes):
            return [float(value) for value in weights]

    if hasattr(strategy, "generate_positions"):
        weights = strategy.generate_positions(bars)
        if isinstance(weights, list) and len(weights) == len(closes):
            return [float(value) for value in weights]

    if callable(strategy):
        resolved: list[float] = []
        for index, close in enumerate(closes):
            value = strategy(index, close)
            resolved.append(float(value))
        return resolved

    return [1.0] + [1.0] * (len(closes) - 1)


def run_vectorized_backtest(
    strategy: Any,
    data: Any,
    *,
    initial_cash: float = 10_000.0,
) -> dict[str, Any]:
    bars = normalize_bars(data)
    closes = closes_from_data(bars)
    if len(closes) < 2:
        return {
            "method": "vectorized",
            "pnl": 0.0,
            "trades": 0,
            "equity_curve": [initial_cash],
            "final_equity": initial_cash,
            "max_drawdown": 0.0,
        }

    returns = pct_returns(closes)
    positions = _resolve_positions(strategy, bars, closes)
    if len(positions) != len(closes):
        positions = [0.0] * len(closes)

    equity = initial_cash
    equity_curve = [equity]
    trades = 0
    for index, bar_return in enumerate(returns):
        weight = positions[index]
        equity *= 1.0 + (weight * bar_return)
        equity_curve.append(equity)
        if index + 1 < len(positions) and positions[index + 1] != weight:
            trades += 1

    final_equity = equity_curve[-1]
    return {
        "method": "vectorized",
        "pnl": final_equity - initial_cash,
        "trades": trades,
        "equity_curve": equity_curve,
        "final_equity": final_equity,
        "return_pct": ((final_equity / initial_cash) - 1.0) * 100.0 if initial_cash else 0.0,
        "max_drawdown": compute_max_drawdown(equity_curve),
    }
