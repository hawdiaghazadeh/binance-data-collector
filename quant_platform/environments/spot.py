"""Spot trading environment (Phase 11)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from quant_platform.environments.common import parse_action


@dataclass
class SpotEnvState:
    step: int
    cash: float
    position: float
    entry_price: float
    price: float
    equity: float


class SpotEnvironmentEngine:
    def __init__(
        self,
        prices: list[float],
        *,
        initial_cash: float = 10_000.0,
        fee_rate: float = 0.001,
    ) -> None:
        if not prices:
            raise ValueError("prices must not be empty")
        if initial_cash <= 0:
            raise ValueError("initial_cash must be > 0")
        if fee_rate < 0:
            raise ValueError("fee_rate must be >= 0")

        self._prices = prices
        self._initial_cash = initial_cash
        self._fee_rate = fee_rate
        self._step = 0
        self._cash = initial_cash
        self._position = 0.0
        self._entry_price = 0.0
        self._prev_equity = initial_cash

    def reset(self) -> dict[str, Any]:
        self._step = 0
        self._cash = self._initial_cash
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
        observation = self._observation()
        info = {"price": price, "step": self._step, "reward_components": {"equity_delta": reward}}
        return observation, reward, done, info

    def _equity(self) -> float:
        price = self._prices[min(self._step, len(self._prices) - 1)]
        return self._cash + self._position * price

    def _observation(self) -> dict[str, Any]:
        price = self._prices[min(self._step, len(self._prices) - 1)]
        return {
            "step": self._step,
            "cash": self._cash,
            "position": self._position,
            "entry_price": self._entry_price,
            "price": price,
            "equity": self._equity(),
            "market": "spot",
        }

    def _execute(self, side: str, size: float, price: float) -> None:
        if side == "hold" or size <= 0 or price <= 0:
            return

        if side == "buy" and self._cash > 0:
            budget = self._cash * size
            fee = budget * self._fee_rate
            units = (budget - fee) / price
            if units <= 0:
                return
            total_cost = self._position * self._entry_price + units * price
            self._position += units
            self._entry_price = total_cost / self._position if self._position else 0.0
            self._cash -= budget

        elif side == "sell" and self._position > 0:
            units = self._position * size
            proceeds = units * price
            fee = proceeds * self._fee_rate
            self._cash += proceeds - fee
            self._position -= units
            if self._position <= 1e-12:
                self._position = 0.0
                self._entry_price = 0.0
