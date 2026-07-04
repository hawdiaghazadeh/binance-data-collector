"""Drawdown penalty reward computation (Phase 9)."""

from __future__ import annotations


def compute_max_drawdown(equity_curve: list[float]) -> float:
    """Maximum drawdown as a positive fraction of peak equity."""
    if not equity_curve:
        return 0.0

    peak = equity_curve[0]
    max_drawdown = 0.0
    for equity in equity_curve:
        peak = max(peak, equity)
        if peak > 0:
            drawdown = (peak - equity) / peak
            max_drawdown = max(max_drawdown, drawdown)
    return max_drawdown


def compute_current_drawdown(equity_curve: list[float]) -> float:
    """Current drawdown from the running peak."""
    if not equity_curve:
        return 0.0

    peak = max(equity_curve)
    current = equity_curve[-1]
    if peak <= 0:
        return 0.0
    return max((peak - current) / peak, 0.0)


def calculate_drawdown_penalty(equity_curve: list[float], *, penalty_factor: float = 1.0) -> float:
    """Negative reward proportional to current drawdown."""
    if penalty_factor < 0:
        raise ValueError("penalty_factor must be >= 0")
    return -compute_current_drawdown(equity_curve) * penalty_factor
