"""Rule-based strategy signal generation (Phase 12)."""

from __future__ import annotations

from typing import Any

from quant_platform.indicators.compute import compute_ema, compute_rsi


def _latest_value(values: list[float | None]) -> float | None:
    for value in reversed(values):
        if value is not None:
            return value
    return None


def _latest_pair(values: list[float | None]) -> tuple[float, float] | None:
    previous: float | None = None
    for value in reversed(values):
        if value is None:
            continue
        if previous is None:
            previous = value
            continue
        return value, previous
    return None


def evaluate_rule_signals(
    closes: list[float],
    *,
    ema: list[float | None] | None = None,
    rsi: list[float | None] | None = None,
    fast_period: int = 9,
    slow_period: int = 21,
    rsi_oversold: float = 30.0,
    rsi_overbought: float = 70.0,
) -> list[dict[str, Any]]:
    """Generate trading signals from indicator rules."""
    if not closes:
        return []

    signals: list[dict[str, Any]] = []
    index = len(closes) - 1

    rsi_series = rsi if rsi is not None else compute_rsi(closes, period=14)
    current_rsi = _latest_value(rsi_series)
    if current_rsi is not None:
        if current_rsi <= rsi_oversold:
            signals.append(
                {
                    "side": "buy",
                    "reason": "rsi_oversold",
                    "source": "rule_based",
                    "index": index,
                    "strength": min((rsi_oversold - current_rsi) / max(rsi_oversold, 1.0), 1.0),
                }
            )
        elif current_rsi >= rsi_overbought:
            signals.append(
                {
                    "side": "sell",
                    "reason": "rsi_overbought",
                    "source": "rule_based",
                    "index": index,
                    "strength": min((current_rsi - rsi_overbought) / max(100.0 - rsi_overbought, 1.0), 1.0),
                }
            )

    fast_ema = ema if ema is not None else compute_ema(closes, fast_period)
    slow_ema = compute_ema(closes, slow_period)
    if len(closes) >= slow_period:
        fast_prev, fast_curr = _extract_last_two(fast_ema)
        slow_prev, slow_curr = _extract_last_two(slow_ema)
        if fast_prev is not None and slow_prev is not None:
            if fast_prev <= slow_prev and fast_curr > slow_curr:
                signals.append(
                    {
                        "side": "buy",
                        "reason": "ema_cross_up",
                        "source": "rule_based",
                        "index": index,
                        "strength": 1.0,
                    }
                )
            elif fast_prev >= slow_prev and fast_curr < slow_curr:
                signals.append(
                    {
                        "side": "sell",
                        "reason": "ema_cross_down",
                        "source": "rule_based",
                        "index": index,
                        "strength": 1.0,
                    }
                )

    return signals


def _extract_last_two(values: list[float | None]) -> tuple[float | None, float | None]:
    found: list[float] = []
    for value in reversed(values):
        if value is None:
            continue
        found.append(value)
        if len(found) == 2:
            return found[1], found[0]
    if len(found) == 1:
        return None, found[0]
    return None, None
