"""Shared environment helpers (Phase 11)."""

from __future__ import annotations

from typing import Any


def parse_action(action: Any) -> tuple[str, float]:
    """Normalize discrete, continuous, or hybrid actions to side + size fraction."""
    if isinstance(action, str):
        side = action.lower()
        if side not in {"hold", "buy", "sell", "long", "short"}:
            raise ValueError(f"Unsupported action: {action!r}")
        if side == "long":
            return "buy", 1.0
        if side == "short":
            return "sell", 1.0
        return side, 0.0 if side == "hold" else 1.0

    if isinstance(action, dict):
        side = str(action.get("side", "hold")).lower()
        size = float(action.get("size", 0.0))
        if side == "long":
            side = "buy"
        elif side == "short":
            side = "sell"
        return side, max(0.0, min(size, 1.0))

    if isinstance(action, (int, float)):
        value = float(action)
        if value > 0.05:
            return "buy", min(abs(value), 1.0)
        if value < -0.05:
            return "sell", min(abs(value), 1.0)
        return "hold", 0.0

    raise TypeError(f"Unsupported action type: {type(action)!r}")


def extract_closes(rows: list[Any]) -> list[float]:
    closes: list[float] = []
    for row in rows:
        if hasattr(row, "close"):
            closes.append(float(getattr(row, "close")))
        elif isinstance(row, dict):
            closes.append(float(row["close"]))
        else:
            closes.append(float(row))
    return closes
