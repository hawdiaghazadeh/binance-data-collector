"""Live trading session engine (Phase 19)."""

from __future__ import annotations

from typing import Any

from quant_platform.backtesting.source import signal_to_action
from quant_platform.brokers.paper import PaperBrokerEngine
from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.live_trading.source import resolve_live_price
from quant_platform.paper_trading.source import closes_from_bars
from quant_platform.portfolios.single import SingleAssetPortfolioEngine
from quant_platform.rewards.drawdown import compute_max_drawdown


class LiveTradingSessionEngine:
    """Live session: exchange feed -> strategy -> broker -> portfolio."""

    def __init__(
        self,
        *,
        strategy: Any,
        exchange: Any,
        bars: list[Any] | None = None,
        symbol: str = "BTCUSDT",
        initial_cash: float = 10_000.0,
        fee_rate: float = 0.001,
        slippage_bps: float = 5.0,
        risk_fraction: float = 0.02,
    ) -> None:
        self._strategy = strategy
        self._exchange = exchange
        self._bars = list(bars or [])
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
        self._tickers: list[dict[str, Any]] = []

    def start(self) -> None:
        self._running = True
        self._fills.clear()
        self._equity_curve.clear()
        self._tickers.clear()
        self._broker = PaperBrokerEngine(
            fee_rate=self._fee_rate,
            slippage_bps=self._slippage_bps,
            order_id_prefix="live",
        )
        self._portfolio.reset()
        if self._exchange is not None and not self._bars:
            ticker = {"symbol": self._symbol}
            if hasattr(self._exchange, "fetch_ticker"):
                ticker = self._exchange.fetch_ticker(self._symbol)
            elif hasattr(self._exchange, "fetch_ticker_price"):
                ticker = self._exchange.fetch_ticker_price(self._symbol)
            self._tickers.append(dict(ticker))

    def stop(self) -> dict[str, Any]:
        if self._bars:
            closes = closes_from_bars(self._bars)
            for index, bar in enumerate(self._bars):
                fallback = closes[index]
                price = resolve_live_price(self._exchange, self._symbol, fallback=fallback)
                ticker = {"symbol": self._symbol, "price": price}
                self._tickers.append(ticker)
                self._process_tick(price=price, klines=self._bars[: index + 1], ticker=ticker)
        elif self._exchange is not None:
            ticker = self._tickers[-1] if self._tickers else {"symbol": self._symbol, "price": 0.0}
            if "price" not in ticker or ticker["price"] == 0.0:
                if hasattr(self._exchange, "fetch_ticker"):
                    ticker = self._exchange.fetch_ticker(self._symbol)
                elif hasattr(self._exchange, "fetch_ticker_price"):
                    ticker = self._exchange.fetch_ticker_price(self._symbol)
            price = float(ticker["price"])
            self._process_tick(price=price, klines=[], ticker=ticker)

        if self._bars:
            final_price = closes_from_bars(self._bars)[-1]
        elif self._tickers:
            final_price = float(self._tickers[-1]["price"])
        else:
            final_price = 0.0

        final_state = self._portfolio.state(price=final_price)
        final_equity = float(final_state.get("equity", self._initial_cash))
        self._running = False
        return {
            "status": "stopped",
            "mode": "live",
            "pnl": final_equity - self._initial_cash,
            "trades": len(self._fills),
            "equity_curve": self._equity_curve,
            "fills": list(self._fills),
            "tickers": list(self._tickers),
            "portfolio_state": final_state,
            "return_pct": ((final_equity / self._initial_cash) - 1.0) * 100.0 if self._initial_cash else 0.0,
            "max_drawdown": compute_max_drawdown(self._equity_curve),
        }

    def _process_tick(
        self,
        *,
        price: float,
        klines: list[Any],
        ticker: dict[str, Any],
    ) -> None:
        ctx = PipelineContext()
        if klines:
            ctx.emit(DataEnvelope(type_key="klines", payload=klines))
        ctx.emit(DataEnvelope(type_key="price", payload=price))
        ctx.emit(DataEnvelope(type_key="ticker", payload=ticker))
        portfolio_state = self._portfolio.state(price=price)
        ctx.emit(DataEnvelope(type_key="portfolio_state", payload=portfolio_state))

        if hasattr(self._strategy, "on_bar") and hasattr(self._strategy, "signals"):
            self._strategy.on_bar(ctx)
            action = signal_to_action(self._strategy.signals(ctx))
        elif callable(self._strategy):
            action = self._strategy(klines[-1] if klines else ticker, len(self._equity_curve), ctx)
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


def run_live_session(config: dict[str, Any]) -> dict[str, Any]:
    engine = LiveTradingSessionEngine(
        strategy=config["strategy"],
        exchange=config.get("exchange"),
        bars=config.get("bars"),
        symbol=str(config.get("symbol", "BTCUSDT")),
        initial_cash=float(config.get("initial_cash", 10_000.0)),
        fee_rate=float(config.get("fee_rate", 0.001)),
        slippage_bps=float(config.get("slippage_bps", 5.0)),
        risk_fraction=float(config.get("risk_fraction", 0.02)),
    )
    engine.start()
    return engine.stop()
