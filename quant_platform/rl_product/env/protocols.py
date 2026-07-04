"""Environment protocols — execution model contract (G33)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class FillResult:
    fill_price: float
    delta_position: float
    fee: float
    spread_cost: float
    slippage_cost: float
    target_exposure: float
    prev_exposure: float


@runtime_checkable
class ExecutionModelProtocol(Protocol):
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
    ) -> FillResult: ...
