"""Evaluation data helpers (Phase 16)."""

from __future__ import annotations

from typing import Any


def normalize_series(data: Any) -> list[Any]:
    if isinstance(data, dict) and "series" in data:
        series = data["series"]
        if isinstance(series, list):
            return list(series)
    if isinstance(data, list):
        return list(data)
    raise TypeError(f"Unsupported evaluation data type: {type(data)!r}")


def extract_returns(data: list[Any]) -> list[float]:
    if not data:
        return []

    first = data[0]
    if isinstance(first, dict):
        if "return" in first:
            return [float(item["return"]) for item in data]
        if "reward" in first:
            return [float(item["reward"]) for item in data]
        if "close" in first:
            closes = [float(item["close"]) for item in data]
            returns: list[float] = []
            for index in range(1, len(closes)):
                prev = closes[index - 1]
                if prev == 0:
                    returns.append(0.0)
                else:
                    returns.append((closes[index] - prev) / prev)
            return returns

    return [float(value) for value in data]
