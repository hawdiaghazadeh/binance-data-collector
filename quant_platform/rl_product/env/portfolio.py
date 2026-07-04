"""Portfolio state tracking for RL environment bridge."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from quant_platform.rl_product.env.protocols import FillResult


@dataclass
class PortfolioTracker:
    market: str
    initial_equity: float
    cash: float
    position: float
    entry_price: float
    leverage: float = 1.0
    peak_equity: float = 0.0
    realized_pnl: float = 0.0
    trade_count: int = 0
    step_pnl: float = 0.0
    _prev_equity: float = field(repr=False, default=0.0)

    @classmethod
    def initial(cls, *, market: str, initial_equity: float, leverage: float = 1.0) -> PortfolioTracker:
        if initial_equity <= 0:
            raise ValueError("initial_equity must be > 0")
        return cls(
            market=market,
            initial_equity=initial_equity,
            cash=initial_equity,
            position=0.0,
            entry_price=0.0,
            leverage=leverage,
            peak_equity=initial_equity,
            _prev_equity=initial_equity,
        )

    def equity(self, price: float) -> float:
        if self.market == "spot":
            return self.cash + self.position * price
        unrealized = self.position * (price - self.entry_price) if self.position else 0.0
        return self.cash + unrealized

    @property
    def drawdown(self) -> float:
        if self.peak_equity <= 0:
            return 0.0
        current = self._prev_equity
        return max(0.0, (self.peak_equity - current) / self.peak_equity)

    @property
    def exposure(self) -> float:
        return abs(self.position)

    def unrealized_pnl(self, price: float) -> float:
        if self.position == 0:
            return 0.0
        if self.market == "spot":
            return self.position * (price - self.entry_price)
        return self.position * (price - self.entry_price)

    def apply_fill(self, fill: FillResult, price: float) -> float:
        """Apply fill and return step PnL (equity delta)."""
        if abs(fill.delta_position) > 1e-12:
            self.trade_count += 1
            self._apply_position_change(fill)

        equity_before = self._prev_equity
        self.cash -= fill.fee
        equity_after = self.equity(price)
        self.step_pnl = equity_after - equity_before
        self.realized_pnl += self.step_pnl
        self._prev_equity = equity_after
        self.peak_equity = max(self.peak_equity, equity_after)
        return self.step_pnl

    def _apply_position_change(self, fill: FillResult) -> None:
        delta = fill.delta_position
        fill_price = fill.fill_price
        if self.market == "spot":
            if delta > 0:
                cost = delta * fill_price
                total_cost = self.position * self.entry_price + cost
                self.position += delta
                self.entry_price = total_cost / self.position if self.position else 0.0
                self.cash -= cost
            elif delta < 0:
                units = min(self.position, abs(delta))
                proceeds = units * fill_price
                self.cash += proceeds
                self.position -= units
                if self.position <= 1e-12:
                    self.position = 0.0
                    self.entry_price = 0.0
            return

        prev = self.position
        new = prev + delta
        if prev == 0 or (prev > 0 and delta > 0) or (prev < 0 and delta < 0):
            total = abs(prev) * abs(self.entry_price) + abs(delta) * fill_price
            self.position = new
            self.entry_price = total / abs(self.position) if self.position else 0.0
        else:
            closed = min(abs(prev), abs(delta)) if prev * delta < 0 else 0.0
            if closed > 0:
                if prev > 0:
                    self.cash += closed * (fill_price - self.entry_price)
                else:
                    self.cash += closed * (self.entry_price - fill_price)
            self.position = new
            if abs(self.position) <= 1e-12:
                self.position = 0.0
                self.entry_price = 0.0
            elif prev * new < 0:
                self.entry_price = fill_price

    def to_dict(self, price: float) -> dict[str, Any]:
        equity = self.equity(price)
        return {
            "initial_equity": self.initial_equity,
            "equity": equity,
            "cash": self.cash,
            "position": self.position,
            "exposure": self.exposure,
            "drawdown": self.drawdown,
            "unrealized_pnl": self.unrealized_pnl(price),
            "upnl": self.unrealized_pnl(price),
            "margin_used": abs(self.position * price) / self.leverage if self.leverage else 0.0,
            "trade_count": self.trade_count,
            "realized_pnl": self.realized_pnl,
            "leverage": self.leverage,
        }

    def reset_step_pnl(self) -> None:
        self.step_pnl = 0.0
