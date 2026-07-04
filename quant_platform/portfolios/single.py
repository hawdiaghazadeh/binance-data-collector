"""Single-asset portfolio engine (Phase 13)."""

from __future__ import annotations

from typing import Any


class SingleAssetPortfolioEngine:
    def __init__(
        self,
        *,
        symbol: str = "BTCUSDT",
        initial_cash: float = 10_000.0,
    ) -> None:
        if initial_cash <= 0:
            raise ValueError("initial_cash must be > 0")
        self._symbol = symbol
        self._initial_cash = initial_cash
        self._cash = initial_cash
        self._quantity = 0.0
        self._entry_price = 0.0
        self._prev_equity = initial_cash

    def state(self, *, price: float) -> dict[str, Any]:
        equity = self._cash + self._quantity * price
        exposure = abs(self._quantity * price) / equity if equity > 0 else 0.0
        unrealized = (price - self._entry_price) * self._quantity if self._quantity else 0.0
        position = {}
        if self._quantity:
            position[self._symbol] = {
                "quantity": self._quantity,
                "entry_price": self._entry_price,
            }
        return {
            "cash": self._cash,
            "equity": equity,
            "exposure": exposure,
            "unrealized_pnl": unrealized,
            "positions": position,
            "symbol": self._symbol,
        }

    def apply_fill(self, fill: dict[str, Any], *, price: float) -> dict[str, Any]:
        if fill.get("status") != "filled":
            return self.state(price=price)

        side = str(fill.get("side", "hold")).lower()
        quantity = float(fill.get("quantity", 0.0))
        fill_price = float(fill.get("fill_price", price))
        fee = float(fill.get("fee", 0.0))

        if side == "buy" and quantity > 0:
            cost = quantity * fill_price + fee
            if cost <= self._cash:
                total_cost = self._entry_price * self._quantity + fill_price * quantity
                self._quantity += quantity
                self._entry_price = total_cost / self._quantity
                self._cash -= cost
        elif side == "sell" and quantity > 0:
            sold = min(quantity, self._quantity)
            proceeds = sold * fill_price - fee
            self._cash += proceeds
            self._quantity -= sold
            if self._quantity == 0:
                self._entry_price = 0.0

        current = self.state(price=price)
        step_pnl = current["equity"] - self._prev_equity
        self._prev_equity = current["equity"]
        current["step_pnl"] = step_pnl
        return current

    def reset(self) -> None:
        self._cash = self._initial_cash
        self._quantity = 0.0
        self._entry_price = 0.0
        self._prev_equity = self._initial_cash
