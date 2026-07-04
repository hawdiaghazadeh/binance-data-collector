"""Paper trading engine plugin (Phase 18)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.plugin import PluginMetadata
from quant_platform.paper_trading.session import PaperTradingSessionEngine

PLUGIN_METADATA = PluginMetadata(
    name="paper_engine",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="End-to-end paper trading session over strategy signals and paper broker fills",
    input_types=["strategy", "klines", "bars", "portfolio_state"],
    output_types=["paper_trading_result", "equity_curve", "portfolio_state"],
    registry_group="platform.paper_trading",
)


class PaperTradingEngine:
    def __init__(self, session: PaperTradingSessionEngine) -> None:
        self._session = session

    def start(self) -> None:
        self._session.start()

    def stop(self) -> dict[str, Any]:
        return self._session.stop()


def factory(*, config: dict | None = None, **kwargs) -> PaperTradingEngine:
    cfg = dict(config or {})
    session = PaperTradingSessionEngine(
        strategy=cfg.get("strategy"),
        bars=cfg.get("bars", []),
        symbol=str(cfg.get("symbol", "BTCUSDT")),
        initial_cash=float(cfg.get("initial_cash", 10_000.0)),
        fee_rate=float(cfg.get("fee_rate", 0.001)),
        slippage_bps=float(cfg.get("slippage_bps", 5.0)),
        risk_fraction=float(cfg.get("risk_fraction", 0.02)),
    )
    return PaperTradingEngine(session)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
