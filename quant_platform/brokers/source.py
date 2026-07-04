"""Broker order helpers (Phase 14)."""

from __future__ import annotations

from typing import Any

from quant_platform.executions.source import normalize_order


def normalize_broker_order(order: Any, *, default_symbol: str = "BTCUSDT") -> dict[str, Any]:
    normalized = normalize_order(order, default_symbol=default_symbol)
    if isinstance(order, dict):
        if "price" in order:
            normalized["price"] = float(order["price"])
        if "equity" in order:
            normalized["equity"] = float(order["equity"])
    return normalized


def next_order_id(prefix: str, counter: int) -> str:
    return f"{prefix}-{counter}"
