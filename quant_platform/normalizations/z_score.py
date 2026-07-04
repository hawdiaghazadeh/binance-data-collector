"""Z-score normalization utilities (Phase 4)."""

from __future__ import annotations

import math
from typing import Any


def _row_numeric(row: object, field: str) -> float:
    if hasattr(row, field):
        return float(getattr(row, field))
    if isinstance(row, dict):
        return float(row[field])
    raise TypeError(f"Unsupported row type: {type(row)!r}")


def extract_numeric_series(rows: list[Any], field: str) -> list[float]:
    return [_row_numeric(row, field) for row in rows]


def compute_z_score(values: list[float], window: int | None = 20) -> list[float | None]:
    """Rolling or population z-score aligned with input values."""
    if not values:
        return []
    if window is not None and window < 1:
        raise ValueError("window must be >= 1")

    result: list[float | None] = [None] * len(values)

    if window is None:
        if len(values) == 1:
            return [0.0]
        mean = sum(values) / len(values)
        variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
        if variance == 0:
            return [0.0 if value == mean else None for value in values]
        std = math.sqrt(variance)
        for index, value in enumerate(values):
            result[index] = (value - mean) / std
        return result

    for index in range(len(values)):
        start = max(0, index - window + 1)
        window_values = values[start : index + 1]
        if len(window_values) < window:
            continue
        mean = sum(window_values) / window
        variance = sum((value - mean) ** 2 for value in window_values) / window
        if variance == 0:
            result[index] = 0.0
        else:
            result[index] = (values[index] - mean) / math.sqrt(variance)
    return result
