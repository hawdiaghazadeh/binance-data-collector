"""MVP execution model — fee, spread, slippage (G33)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from quant_platform.rl_product.env.protocols import FillResult


@dataclass(slots=True)
class ExecutionConfig:
    fee_bps: float = 10.0
    spread_bps: float = 5.0
    slippage_bps: float = 3.0
    partial_fill: bool = False

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> ExecutionConfig:
        execution = config.get("execution", config)
        return cls(
            fee_bps=float(execution.get("fee_bps", 10.0)),
            spread_bps=float(execution.get("spread_bps", 5.0)),
            slippage_bps=float(execution.get("slippage_bps", 3.0)),
            partial_fill=bool(execution.get("partial_fill", False)),
        )


class SimpleExecutionModel:
    """Pluggable MVP execution — affects PnL only, not observations."""

    __slots__ = ("_config",)

    def __init__(self, config: ExecutionConfig | None = None) -> None:
        self._config = config or ExecutionConfig()

    @property
    def config(self) -> ExecutionConfig:
        return self._config

    def _current_exposure(
        self,
        *,
        position: float,
        price: float,
        equity: float,
        market: str,
        leverage: float,
    ) -> float:
        if equity <= 0 or price <= 0:
            return 0.0
        if market == "spot":
            return max(0.0, min(1.0, (position * price) / equity))
        max_notional = equity * leverage
        if max_notional <= 0:
            return 0.0
        return max(-1.0, min(1.0, (position * price) / max_notional))

    def simulate_fill(
        self,
        *,
        target_exposure: float,
        price: float,
        position: float,
        equity: float,
        bar_volume: float,
        market: str,
        leverage: float = 1.0,
    ) -> FillResult:
        if price <= 0 or equity <= 0:
            return FillResult(
                fill_price=price,
                delta_position=0.0,
                fee=0.0,
                spread_cost=0.0,
                slippage_cost=0.0,
                target_exposure=target_exposure,
                prev_exposure=0.0,
            )

        if market == "spot":
            target_exposure = max(0.0, min(1.0, target_exposure))
        else:
            target_exposure = max(-1.0, min(1.0, target_exposure))

        prev_exposure = self._current_exposure(
            position=position,
            price=price,
            equity=equity,
            market=market,
            leverage=leverage,
        )
        delta_exposure = target_exposure - prev_exposure
        if abs(delta_exposure) < 1e-9:
            return FillResult(
                fill_price=price,
                delta_position=0.0,
                fee=0.0,
                spread_cost=0.0,
                slippage_cost=0.0,
                target_exposure=target_exposure,
                prev_exposure=prev_exposure,
            )

        direction = 1.0 if delta_exposure > 0 else -1.0
        spread_half = price * (self._config.spread_bps / 10_000.0) / 2.0
        slippage = price * (self._config.slippage_bps / 10_000.0) * abs(delta_exposure)
        fill_price = price + direction * (spread_half + slippage)
        spread_cost = spread_half * abs(delta_exposure)
        slippage_cost = slippage * abs(delta_exposure)

        if market == "spot":
            target_value = target_exposure * equity
            current_value = position * price
            delta_value = target_value - current_value
            delta_position = delta_value / fill_price if fill_price > 0 else 0.0
            if not self._config.partial_fill and delta_exposure > 0:
                max_buy_value = max(equity - current_value, 0.0)
                delta_value = min(delta_value, max_buy_value)
                delta_position = delta_value / fill_price if fill_price > 0 else 0.0
        else:
            max_notional = equity * leverage
            target_notional = target_exposure * max_notional
            current_notional = position * price
            delta_notional = target_notional - current_notional
            delta_position = delta_notional / fill_price if fill_price > 0 else 0.0

        trade_notional = abs(delta_position * fill_price)
        fee = trade_notional * (self._config.fee_bps / 10_000.0)

        return FillResult(
            fill_price=fill_price,
            delta_position=delta_position,
            fee=fee,
            spread_cost=spread_cost,
            slippage_cost=slippage_cost,
            target_exposure=target_exposure,
            prev_exposure=prev_exposure,
        )
