"""Risk observation plugin (Phase 8)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.plugin import PluginMetadata
from quant_platform.observations.risk import build_risk_observation

PLUGIN_METADATA = PluginMetadata(
    name="risk_observation",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Risk metrics observation from portfolio and ATR context",
    input_types=["portfolio_state", "atr", "risk_state"],
    output_types=["risk_observation"],
    registry_group="platform.observations",
)


class RiskObservation:
    def __init__(self, max_exposure: float = 1.0) -> None:
        self._max_exposure = max_exposure

    def build(self, ctx: PipelineContext) -> dict[str, Any]:
        observation = build_risk_observation(ctx, max_exposure=self._max_exposure)
        ctx.emit(
            DataEnvelope(
                type_key="risk_observation",
                payload=observation,
                metadata={"max_exposure": self._max_exposure},
            )
        )
        return observation


def factory(*, max_exposure: float = 1.0, config: dict | None = None, **kwargs) -> RiskObservation:
    if config and "max_exposure" in config:
        max_exposure = float(config["max_exposure"])
    return RiskObservation(max_exposure=max_exposure)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
