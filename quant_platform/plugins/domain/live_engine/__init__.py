"""Live trading engine plugin (Phase 19)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.plugin import PluginMetadata
from quant_platform.exchanges.binance import BinanceRestClient
from quant_platform.live_trading.session import LiveTradingSessionEngine
from quant_platform.plugins.domain.binance_exchange import BinanceExchange

PLUGIN_METADATA = PluginMetadata(
    name="live_engine",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Live trading session wired to exchange feed and paper broker routing",
    input_types=["strategy", "exchange", "ticker", "klines"],
    output_types=["live_trading_result", "equity_curve", "portfolio_state"],
    registry_group="platform.live_trading",
)


class LiveTradingEngine:
    def __init__(self, session: LiveTradingSessionEngine) -> None:
        self._session = session
        self._summary: dict[str, Any] = {}

    def start(self) -> None:
        self._session.start()

    def stop(self) -> None:
        self._summary = self._session.stop()

    @property
    def summary(self) -> dict[str, Any]:
        return dict(self._summary)


def factory(*, config: dict | None = None, **kwargs) -> LiveTradingEngine:
    cfg = dict(config or {})
    exchange = cfg.get("exchange")
    if exchange is None:
        client = cfg.get("client")
        if client is None and cfg.get("base_url"):
            client = BinanceRestClient(base_url=str(cfg["base_url"]))
        elif client is None:
            client = cfg.get("exchange_client")
        if client is not None:
            exchange = BinanceExchange(client)

    session = LiveTradingSessionEngine(
        strategy=cfg.get("strategy"),
        exchange=exchange,
        bars=cfg.get("bars"),
        symbol=str(cfg.get("symbol", "BTCUSDT")),
        initial_cash=float(cfg.get("initial_cash", 10_000.0)),
        fee_rate=float(cfg.get("fee_rate", 0.001)),
        slippage_bps=float(cfg.get("slippage_bps", 5.0)),
        risk_fraction=float(cfg.get("risk_fraction", 0.02)),
    )
    return LiveTradingEngine(session)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
