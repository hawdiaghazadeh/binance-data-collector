"""Indicator computation utilities (Phase 5)."""

from __future__ import annotations


def row_close(row: object) -> float:
    if hasattr(row, "close"):
        return float(getattr(row, "close"))
    if isinstance(row, dict):
        return float(row["close"])
    raise TypeError(f"Unsupported row type: {type(row)!r}")


def extract_closes(rows: list[object]) -> list[float]:
    return [row_close(row) for row in rows]


def compute_ema(values: list[float], period: int) -> list[float | None]:
    """Exponential moving average aligned with input values."""
    if period < 1:
        raise ValueError("period must be >= 1")
    if not values:
        return []

    result: list[float | None] = [None] * len(values)
    if len(values) < period:
        return result

    multiplier = 2.0 / (period + 1)
    seed = sum(values[:period]) / period
    result[period - 1] = seed
    previous = seed
    for index in range(period, len(values)):
        previous = (values[index] - previous) * multiplier + previous
        result[index] = previous
    return result


def compute_rsi(closes: list[float], period: int = 14) -> list[float | None]:
    """Wilder-smoothed RSI aligned with input closes."""
    if period < 1:
        raise ValueError("period must be >= 1")
    if not closes:
        return []

    result: list[float | None] = [None] * len(closes)
    if len(closes) <= period:
        return result

    gains: list[float] = []
    losses: list[float] = []
    for index in range(1, len(closes)):
        change = closes[index] - closes[index - 1]
        gains.append(max(change, 0.0))
        losses.append(max(-change, 0.0))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    result[period] = _rsi_from_averages(avg_gain, avg_loss)

    for index in range(period + 1, len(closes)):
        change_index = index - 1
        avg_gain = (avg_gain * (period - 1) + gains[change_index]) / period
        avg_loss = (avg_loss * (period - 1) + losses[change_index]) / period
        result[index] = _rsi_from_averages(avg_gain, avg_loss)
    return result


def _rsi_from_averages(avg_gain: float, avg_loss: float) -> float:
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def compute_macd(
    closes: list[float],
    *,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[list[float | None], list[float | None], list[float | None]]:
    """MACD line, signal line, and histogram aligned with input closes."""
    if fast < 1 or slow < 1 or signal < 1:
        raise ValueError("MACD periods must be >= 1")
    if fast >= slow:
        raise ValueError("fast period must be less than slow period")
    if not closes:
        return [], [], []

    fast_ema = compute_ema(closes, fast)
    slow_ema = compute_ema(closes, slow)
    macd_line: list[float | None] = [None] * len(closes)
    for index in range(len(closes)):
        if fast_ema[index] is not None and slow_ema[index] is not None:
            macd_line[index] = fast_ema[index] - slow_ema[index]

    signal_line: list[float | None] = [None] * len(closes)
    histogram: list[float | None] = [None] * len(closes)

    macd_values: list[float] = []
    macd_indices: list[int] = []
    for index, value in enumerate(macd_line):
        if value is not None:
            macd_values.append(value)
            macd_indices.append(index)

    if len(macd_values) >= signal:
        signal_ema = compute_ema(macd_values, signal)
        for offset, index in enumerate(macd_indices):
            signal_value = signal_ema[offset]
            if signal_value is not None:
                signal_line[index] = signal_value
                macd_value = macd_line[index]
                assert macd_value is not None
                histogram[index] = macd_value - signal_value

    return macd_line, signal_line, histogram
