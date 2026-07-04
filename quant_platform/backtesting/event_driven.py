"""Event-driven backtest engine (Phase 17)."""

from __future__ import annotations

from typing import Any

from quant_platform.backtesting.source import normalize_bars, signal_to_action
from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.environments.common import extract_closes, parse_action
from quant_platform.rewards.drawdown import compute_max_drawdown


class _BacktestPortfolio:
    def __init__(self, *, initial_cash: float, fee_rate: float) -> None:
        self.cash = initial_cash
        self.position = 0.0
        self.entry_price = 0.0
        self.fee_rate = fee_rate
        self.trades = 0

    def execute(self, action: Any, price: float) -> None:
        side, size = parse_action(action)
        if side == "hold" or size <= 0 or price <= 0:
            return

        if side == "buy" and self.cash > 0:
            budget = self.cash * size
            fee = budget * self.fee_rate
            units = (budget - fee) / price
            if units <= 0:
                return
            total_cost = self.position * self.entry_price + units * price
            self.position += units
            self.entry_price = total_cost / self.position
            self.cash -= budget
            self.trades += 1
        elif side == "sell" and self.position > 0:
            units = self.position * size
            proceeds = units * price
            fee = proceeds * self.fee_rate
            self.cash += proceeds - fee
            self.position -= units
            if self.position <= 1e-12:
                self.position = 0.0
                self.entry_price = 0.0
            self.trades += 1

    def equity(self, price: float) -> float:
        return self.cash + self.position * price


def run_event_driven_backtest(
    strategy: Any,
    data: Any,
    *,
    initial_cash: float = 10_000.0,
    fee_rate: float = 0.001,
) -> dict[str, Any]:
    bars = normalize_bars(data)
    if not bars:
        return {
            "method": "event_driven",
            "pnl": 0.0,
            "trades": 0,
            "equity_curve": [],
            "final_equity": initial_cash,
            "max_drawdown": 0.0,
        }

    closes = extract_closes(bars)
    portfolio = _BacktestPortfolio(initial_cash=initial_cash, fee_rate=fee_rate)
    equity_curve = [portfolio.equity(closes[0])]

    for index in range(len(bars)):
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="klines", payload=bars[: index + 1]))

        if hasattr(strategy, "on_bar") and hasattr(strategy, "signals"):
            strategy.on_bar(ctx)
            action = signal_to_action(strategy.signals(ctx))
        elif callable(strategy):
            action = strategy(bars[index], index, ctx)
        else:
            action = {"side": "hold", "size": 0.0}

        portfolio.execute(action, closes[index])
        equity_curve.append(portfolio.equity(closes[index]))

    final_equity = equity_curve[-1]
    return {
        "method": "event_driven",
        "pnl": final_equity - initial_cash,
        "trades": portfolio.trades,
        "equity_curve": equity_curve,
        "final_equity": final_equity,
        "return_pct": ((final_equity / initial_cash) - 1.0) * 100.0 if initial_cash else 0.0,
        "max_drawdown": compute_max_drawdown(equity_curve),
    }
