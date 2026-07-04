"""Futures trading environment (Phase 11)."""

from __future__ import annotations

from typing import Any

from quant_platform.environments.common import parse_action


class FuturesEnvironmentEngine:
    def __init__(
        self,
        prices: list[float],
        *,
        initial_margin: float = 10_000.0,
        leverage: float = 5.0,
        fee_rate: float = 0.0005,
        maintenance_margin_ratio: float = 0.05,
    ) -> None:
        if not prices:
            raise ValueError("prices must not be empty")
        if initial_margin <= 0:
            raise ValueError("initial_margin must be > 0")
        if leverage <= 0:
            raise ValueError("leverage must be > 0")
        if fee_rate < 0:
            raise ValueError("fee_rate must be >= 0")
        if maintenance_margin_ratio <= 0:
            raise ValueError("maintenance_margin_ratio must be > 0")

        self._prices = prices
        self._initial_margin = initial_margin
        self._leverage = leverage
        self._fee_rate = fee_rate
        self._maintenance_margin_ratio = maintenance_margin_ratio
        self._step = 0
        self._margin = initial_margin
        self._position = 0.0
        self._entry_price = 0.0
        self._prev_equity = initial_margin

    def reset(self) -> dict[str, Any]:
        self._step = 0
        self._margin = self._initial_margin
        self._position = 0.0
        self._entry_price = 0.0
        self._prev_equity = self._equity()
        return self._observation()

    def step(self, action: Any) -> tuple[dict[str, Any], float, bool, dict[str, Any]]:
        price = self._prices[self._step]
        side, size = parse_action(action)
        self._execute(side, size, price)
        equity = self._equity()
        reward = equity - self._prev_equity
        self._prev_equity = equity

        self._step += 1
        done = self._step >= len(self._prices) - 1
        liquidated = equity <= self._maintenance_requirement(price)
        if liquidated:
            done = True
            self._margin = max(equity, 0.0)
            self._position = 0.0
            self._entry_price = 0.0

        observation = self._observation()
        info = {
            "price": price,
            "step": self._step,
            "liquidated": liquidated,
            "leverage": self._leverage,
        }
        return observation, reward, done, info

    def _maintenance_requirement(self, price: float) -> float:
        notional = abs(self._position) * price
        return notional * self._maintenance_margin_ratio

    def _equity(self) -> float:
        price = self._prices[min(self._step, len(self._prices) - 1)]
        unrealized = self._position * (price - self._entry_price) if self._position else 0.0
        return self._margin + unrealized

    def _observation(self) -> dict[str, Any]:
        price = self._prices[min(self._step, len(self._prices) - 1)]
        unrealized = self._position * (price - self._entry_price) if self._position else 0.0
        return {
            "step": self._step,
            "margin": self._margin,
            "position": self._position,
            "entry_price": self._entry_price,
            "price": price,
            "equity": self._equity(),
            "unrealized_pnl": unrealized,
            "leverage": self._leverage,
            "market": "futures",
        }

    def _execute(self, side: str, size: float, price: float) -> None:
        if side == "hold" or size <= 0 or price <= 0:
            return

        target_notional = self._margin * self._leverage * size
        target_units = target_notional / price
        fee = target_notional * self._fee_rate
        self._margin -= fee

        if side == "buy":
            if self._position < 0:
                self._close_partial(min(abs(self._position), target_units), price)
            self._open_long(target_units, price)
        elif side == "sell":
            if self._position > 0:
                self._close_partial(min(self._position, target_units), price)
            self._open_short(target_units, price)

    def _open_long(self, units: float, price: float) -> None:
        if units <= 0:
            return
        total = self._position * self._entry_price + units * price
        self._position += units
        self._entry_price = total / self._position if self._position else 0.0

    def _open_short(self, units: float, price: float) -> None:
        if units <= 0:
            return
        if self._position > 0:
            units = min(units, self._position)
        abs_total = abs(self._position) * abs(self._entry_price) + units * price
        self._position -= units
        self._entry_price = abs_total / abs(self._position) if self._position else 0.0

    def _close_partial(self, units: float, price: float) -> None:
        if units <= 0 or self._position == 0:
            return
        if self._position > 0:
            closed = min(units, self._position)
            pnl = closed * (price - self._entry_price)
            self._margin += pnl
            self._position -= closed
        else:
            closed = min(units, abs(self._position))
            pnl = closed * (self._entry_price - price)
            self._margin += pnl
            self._position += closed
        if abs(self._position) <= 1e-12:
            self._position = 0.0
            self._entry_price = 0.0
