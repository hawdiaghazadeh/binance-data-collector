"""Portfolio state block for RL observation."""

from __future__ import annotations

import math
from typing import Any


def _clip(value: float, lo: float = -5.0, hi: float = 5.0) -> float:
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return max(lo, min(hi, value))


def build_portfolio_block(state: dict[str, Any] | None, *, portfolio_dims: int) -> list[float]:
    """Normalize portfolio fields into a fixed-size block."""
    if portfolio_dims < 1:
        raise ValueError("portfolio_dims must be >= 1")

    s = state or {}
    initial_equity = float(s.get("initial_equity", 1.0)) or 1.0
    equity = float(s.get("equity", initial_equity))
    position = float(s.get("position", 0.0))
    upnl = float(s.get("unrealized_pnl", s.get("upnl", 0.0)))
    margin = float(s.get("margin_used", 0.0))
    drawdown = float(s.get("drawdown", 0.0))
    exposure = float(s.get("exposure", abs(position)))
    cash = float(s.get("cash", equity))
    trades = float(s.get("trade_count", 0.0))
    time_in_pos = float(s.get("time_in_position", 0.0))
    entry_dist = float(s.get("avg_entry_dist", 0.0))
    risk_util = float(s.get("risk_utilization", 0.0))
    win_rate = float(s.get("win_rate", 0.0))
    lev = float(s.get("leverage", 1.0))

    fields = [
        _clip(position),
        _clip(equity / initial_equity - 1.0),
        _clip(upnl / initial_equity),
        _clip(margin / initial_equity),
        _clip(drawdown),
        _clip(exposure),
        _clip(cash / initial_equity - 1.0),
        _clip(trades / 100.0),
        _clip(time_in_pos / 500.0),
        _clip(entry_dist),
        _clip(risk_util),
        _clip(win_rate),
        _clip(lev / 10.0),
        _clip(float(s.get("realized_pnl", 0.0)) / initial_equity),
    ]

    if len(fields) >= portfolio_dims:
        return fields[:portfolio_dims]

    padded = fields + [0.0] * (portfolio_dims - len(fields))
    return padded
