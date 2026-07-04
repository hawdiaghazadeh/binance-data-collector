"""Paper trading session helpers (Phase 18)."""

from __future__ import annotations

from typing import Any

from quant_platform.backtesting.source import normalize_bars
from quant_platform.environments.common import extract_closes


def session_config(
    *,
    strategy: Any,
    bars: list[Any],
    symbol: str = "BTCUSDT",
    initial_cash: float = 10_000.0,
    fee_rate: float = 0.001,
    slippage_bps: float = 5.0,
    risk_fraction: float = 0.02,
) -> dict[str, Any]:
    return {
        "strategy": strategy,
        "bars": normalize_bars(bars),
        "symbol": symbol,
        "initial_cash": initial_cash,
        "fee_rate": fee_rate,
        "slippage_bps": slippage_bps,
        "risk_fraction": risk_fraction,
    }


def closes_from_bars(bars: list[Any]) -> list[float]:
    return extract_closes(bars)
