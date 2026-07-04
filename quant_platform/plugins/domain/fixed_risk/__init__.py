"""Fixed fractional risk plugin (Phase 13)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import PipelineContext
from quant_platform.core.plugin import PluginMetadata
from quant_platform.risks.fixed import check_fixed_risk, fixed_position_size

PLUGIN_METADATA = PluginMetadata(
    name="fixed_risk",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Fixed fractional position sizing with exposure cap",
    input_types=["portfolio_state", "order"],
    output_types=["risk_state"],
    registry_group="platform.risks",
)


class FixedRisk:
    def __init__(
        self,
        *,
        risk_fraction: float = 0.02,
        max_exposure: float = 1.0,
        max_order_size: float = 1.0,
    ) -> None:
        self._risk_fraction = risk_fraction
        self._max_exposure = max_exposure
        self._max_order_size = max_order_size

    def check(self, ctx: PipelineContext, order: Any) -> bool:
        return check_fixed_risk(
            ctx,
            order,
            max_exposure=self._max_exposure,
            max_order_size=self._max_order_size,
        )

    def position_size(self, ctx: PipelineContext) -> float:
        return fixed_position_size(
            ctx,
            risk_fraction=self._risk_fraction,
            max_size=self._max_order_size,
        )


def factory(
    *,
    risk_fraction: float = 0.02,
    max_exposure: float = 1.0,
    max_order_size: float = 1.0,
    config: dict | None = None,
    **kwargs,
) -> FixedRisk:
    if config:
        risk_fraction = float(config.get("risk_fraction", risk_fraction))
        max_exposure = float(config.get("max_exposure", max_exposure))
        max_order_size = float(config.get("max_order_size", max_order_size))
    return FixedRisk(
        risk_fraction=risk_fraction,
        max_exposure=max_exposure,
        max_order_size=max_order_size,
    )


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
