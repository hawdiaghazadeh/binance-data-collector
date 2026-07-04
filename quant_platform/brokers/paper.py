"""Paper broker engine (Phase 14)."""

from __future__ import annotations

from typing import Any

from quant_platform.brokers.source import next_order_id, normalize_broker_order
from quant_platform.executions.simulation import simulate_fill


class PaperBrokerEngine:
    def __init__(
        self,
        *,
        fee_rate: float = 0.001,
        slippage_bps: float = 5.0,
        order_id_prefix: str = "paper",
    ) -> None:
        self._fee_rate = fee_rate
        self._slippage_bps = slippage_bps
        self._order_id_prefix = order_id_prefix
        self._counter = 0
        self._orders: dict[str, dict[str, Any]] = {}

    def submit_order(
        self,
        order: Any,
        *,
        price: float,
        equity: float = 10_000.0,
    ) -> dict[str, Any]:
        normalized = normalize_broker_order(order)
        side = normalized.get("side", "hold")
        if side == "hold":
            self._counter += 1
            order_id = next_order_id(self._order_id_prefix, self._counter)
            record = {"order_id": order_id, "status": "skipped", "reason": "hold"}
            self._orders[order_id] = record
            return record

        fill = simulate_fill(
            normalized,
            price=price,
            equity=equity,
            fee_rate=self._fee_rate,
            slippage_bps=self._slippage_bps,
        )
        self._counter += 1
        order_id = next_order_id(self._order_id_prefix, self._counter)
        record = {
            "order_id": order_id,
            "status": fill.get("status", "filled"),
            "fill": fill,
        }
        self._orders[order_id] = record
        return record

    def cancel_order(self, order_id: str) -> bool:
        record = self._orders.get(order_id)
        if record is None:
            return False
        if record.get("status") == "filled":
            return False
        record["status"] = "cancelled"
        return True

    def get_order(self, order_id: str) -> dict[str, Any] | None:
        record = self._orders.get(order_id)
        return dict(record) if record is not None else None
