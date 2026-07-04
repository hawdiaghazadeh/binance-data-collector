"""Paper trading session engine (Phase 18)."""

from __future__ import annotations

from typing import Any

from quant_platform.backtesting.source import signal_to_action
from quant_platform.brokers.paper import PaperBrokerEngine
from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.paper_trading.source import closes_from_bars
from quant_platform.portfolios.single import SingleAssetPortfolioEngine
from quant_platform.rewards.drawdown import compute_max_drawdown


class PaperTradingSessionEngine:
    """End-to-end paper session: strategy -> broker -> portfolio."""

    def __init__(
        self,
        *,
        strategy: Any,
        bars: list[Any],
        symbol: str = "BTCUSDT",
        initial_cash: float = 10_000.0,
        fee_rate: float = 0.001,
        slippage_bps: float = 5.0,
        risk_fraction: float = 0.02,
    ) -> None:
        self._strategy = strategy
        self._bars = list(bars)
        self._symbol = symbol
        self._initial_cash = initial_cash
        self._fee_rate = fee_rate
        self._slippage_bps = slippage_bps
        self._risk_fraction = risk_fraction
        self._broker = PaperBrokerEngine(fee_rate=fee_rate, slippage_bps=slippage_bps)
        self._portfolio = SingleAssetPortfolioEngine(symbol=symbol, initial_cash=initial_cash)
        self._running = False
        self._fills: list[dict[str, Any]] = []
        self._equity_curve: list[float] = []

    def start(self) -> None:
        self._running = True
        self._fills.clear()
        self._equity_curve.clear()
        self._broker = PaperBrokerEngine(
            fee_rate=self._fee_rate,
            slippage_bps=self._slippage_bps,
        )
        self._portfolio.reset()

    def stop(self) -> dict[str, Any]:
        if not self._bars:
            return {
                "status": "stopped",
                "pnl": 0.0,
                "trades": 0,
                "equity_curve": [],
                "fills": [],
                "portfolio_state": self._portfolio.state(price=0.0),
                "max_drawdown": 0.0,
            }

        closes = closes_from_bars(self._bars)
        for index in range(len(self._bars)):
            price = closes[index]
            ctx = PipelineContext()
            ctx.emit(DataEnvelope(type_key="klines", payload=self._bars[: index + 1]))
            ctx.emit(DataEnvelope(type_key="price", payload=price))
            portfolio_state = self._portfolio.state(price=price)
            ctx.emit(DataEnvelope(type_key="portfolio_state", payload=portfolio_state))

            if hasattr(self._strategy, "on_bar") and hasattr(self._strategy, "signals"):
                self._strategy.on_bar(ctx)
                action = signal_to_action(self._strategy.signals(ctx))
            elif callable(self._strategy):
                action = self._strategy(self._bars[index], index, ctx)
            else:
                action = {"side": "hold", "size": 0.0}

            if action.get("side") != "hold" and float(action.get("size", 0.0)) > 0:
                action = dict(action)
                action["size"] = min(float(action["size"]), self._risk_fraction)
                action["symbol"] = self._symbol
                equity = float(portfolio_state.get("equity", self._initial_cash))
                result = self._broker.submit_order(action, price=price, equity=equity)
                fill = result.get("fill")
                if isinstance(fill, dict) and fill.get("status") == "filled":
                    self._fills.append(result)
                    portfolio_state = self._portfolio.apply_fill(fill, price=price)

            self._equity_curve.append(float(portfolio_state.get("equity", price)))

        final_state = self._portfolio.state(price=closes[-1])
        final_equity = float(final_state.get("equity", self._initial_cash))
        self._running = False
        return {
            "status": "stopped",
            "pnl": final_equity - self._initial_cash,
            "trades": len(self._fills),
            "equity_curve": self._equity_curve,
            "fills": list(self._fills),
            "portfolio_state": final_state,
            "return_pct": ((final_equity / self._initial_cash) - 1.0) * 100.0 if self._initial_cash else 0.0,
            "max_drawdown": compute_max_drawdown(self._equity_curve),
        }


def run_paper_session(config: dict[str, Any]) -> dict[str, Any]:
    engine = PaperTradingSessionEngine(
        strategy=config["strategy"],
        bars=config.get("bars", []),
        symbol=str(config.get("symbol", "BTCUSDT")),
        initial_cash=float(config.get("initial_cash", 10_000.0)),
        fee_rate=float(config.get("fee_rate", 0.001)),
        slippage_bps=float(config.get("slippage_bps", 5.0)),
        risk_fraction=float(config.get("risk_fraction", 0.02)),
    )
    engine.start()
    return engine.stop()
