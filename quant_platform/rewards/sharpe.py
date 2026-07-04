"""Sharpe ratio reward computation (Phase 9)."""

from __future__ import annotations

import math


def compute_sharpe_ratio(returns: list[float], *, risk_free: float = 0.0) -> float:
    """Sample Sharpe ratio from a return series."""
    if len(returns) < 2:
        return 0.0

    mean = sum(returns) / len(returns)
    variance = sum((value - mean) ** 2 for value in returns) / (len(returns) - 1)
    if variance == 0:
        return 0.0
    std = math.sqrt(variance)
    return (mean - risk_free) / std


def calculate_sharpe_reward(returns: list[float], *, window: int = 20, risk_free: float = 0.0) -> float:
    """Rolling Sharpe reward from the most recent returns."""
    if window < 2:
        raise ValueError("window must be >= 2")
    if len(returns) < window:
        return compute_sharpe_ratio(returns, risk_free=risk_free)
    return compute_sharpe_ratio(returns[-window:], risk_free=risk_free)
