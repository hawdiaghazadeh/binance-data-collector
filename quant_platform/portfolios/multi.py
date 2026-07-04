"""Multi-asset portfolio engine (Phase 13)."""

from __future__ import annotations

from typing import Any


class MultiAssetPortfolioEngine:
    def __init__(self, *, initial_cash: float = 10_000.0) -> None:
        if initial_cash <= 0:
            raise ValueError("initial_cash must be > 0")
        self._initial_cash = initial_cash
        self._cash = initial_cash
        self._positions: dict[str, dict[str, float]] = {}
        self._prev_equity = initial_cash

    def state(self, *, prices: dict[str, float]) -> dict[str, Any]:
        positions: dict[str, dict[str, float]] = {}
        market_value = 0.0
        unrealized = 0.0

        for symbol, pos in self._positions.items():
            quantity = pos["quantity"]
            entry = pos["entry_price"]
            price = prices.get(symbol, entry)
            positions[symbol] = {"quantity": quantity, "entry_price": entry, "price": price}
            market_value += quantity * price
            unrealized += (price - entry) * quantity

        equity = self._cash + market_value
        exposure = market_value / equity if equity > 0 else 0.0
        return {
            "cash": self._cash,
            "equity": equity,
            "exposure": exposure,
            "unrealized_pnl": unrealized,
            "positions": positions,
        }

    def apply_fill(self, fill: dict[str, Any], *, prices: dict[str, float]) -> dict[str, Any]:
        if fill.get("status") != "filled":
            symbol = str(fill.get("symbol", "BTCUSDT"))
            price = prices.get(symbol, 0.0)
            return self.state(prices=prices)

        symbol = str(fill.get("symbol", "BTCUSDT"))
        side = str(fill.get("side", "hold")).lower()
        quantity = float(fill.get("quantity", 0.0))
        fill_price = float(fill.get("fill_price", prices.get(symbol, 0.0)))
        fee = float(fill.get("fee", 0.0))

        if side == "buy" and quantity > 0:
            cost = quantity * fill_price + fee
            if cost <= self._cash:
                pos = self._positions.get(symbol, {"quantity": 0.0, "entry_price": 0.0})
                old_qty = pos["quantity"]
                if old_qty == 0:
                    pos["entry_price"] = fill_price
                    pos["quantity"] = quantity
                else:
                    total = pos["entry_price"] * old_qty + fill_price * quantity
                    pos["quantity"] = old_qty + quantity
                    pos["entry_price"] = total / pos["quantity"]
                self._positions[symbol] = pos
                self._cash -= cost
        elif side == "sell" and quantity > 0:
            pos = self._positions.get(symbol)
            if pos:
                sold = min(quantity, pos["quantity"])
                proceeds = sold * fill_price - fee
                self._cash += proceeds
                pos["quantity"] -= sold
                if pos["quantity"] <= 0:
                    del self._positions[symbol]
                else:
                    self._positions[symbol] = pos

        current = self.state(prices=prices)
        step_pnl = current["equity"] - self._prev_equity
        self._prev_equity = current["equity"]
        current["step_pnl"] = step_pnl
        return current

    def reset(self) -> None:
        self._cash = self._initial_cash
        self._positions.clear()
        self._prev_equity = self._initial_cash
