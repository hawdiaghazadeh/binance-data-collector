"""Backtest data helpers (Phase 17)."""

from __future__ import annotations

from typing import Any

from quant_platform.environments.common import extract_closes


def normalize_bars(data: Any) -> list[Any]:
    if isinstance(data, dict):
        if "bars" in data and isinstance(data["bars"], list):
            return list(data["bars"])
        if "klines" in data and isinstance(data["klines"], list):
            return list(data["klines"])
        if "series" in data and isinstance(data["series"], list):
            return list(data["series"])
    if isinstance(data, list):
        return list(data)
    raise TypeError(f"Unsupported backtest data type: {type(data)!r}")


def closes_from_data(data: Any) -> list[float]:
    return extract_closes(normalize_bars(data))


def pct_returns(closes: list[float]) -> list[float]:
    if len(closes) < 2:
        return []
    returns: list[float] = []
    for index in range(1, len(closes)):
        prev = closes[index - 1]
        if prev == 0:
            returns.append(0.0)
        else:
            returns.append((closes[index] - prev) / prev)
    return returns


def signal_to_action(signals: list[dict[str, Any]]) -> dict[str, Any]:
    if not signals:
        return {"side": "hold", "size": 0.0}
    latest = signals[-1]
    side = str(latest.get("side", "hold")).lower()
    if side == "long":
        side = "buy"
    elif side == "short":
        side = "sell"
    return {"side": side, "size": float(latest.get("size", 1.0))}
