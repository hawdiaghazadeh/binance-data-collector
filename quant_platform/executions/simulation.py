"""Simulated order execution (Phase 13)."""

from __future__ import annotations

from typing import Any


def simulate_fill(
    order: dict[str, Any],
    *,
    price: float,
    equity: float,
    fee_rate: float = 0.001,
    slippage_bps: float = 5.0,
) -> dict[str, Any]:
    side = str(order.get("side", "hold")).lower()
    if side == "hold":
        return {"status": "skipped", "order": order, "reason": "hold"}

    size_fraction = float(order.get("size", 0.0))
    if size_fraction <= 0:
        return {"status": "skipped", "order": order, "reason": "zero_size"}

    slip = price * (slippage_bps / 10_000.0)
    fill_price = price + slip if side == "buy" else price - slip
    notional = equity * size_fraction
    quantity = notional / fill_price if fill_price > 0 else 0.0
    fee = notional * fee_rate

    return {
        "status": "filled",
        "order": order,
        "symbol": order.get("symbol"),
        "side": side,
        "fill_price": fill_price,
        "quantity": quantity,
        "notional": notional,
        "fee": fee,
    }
