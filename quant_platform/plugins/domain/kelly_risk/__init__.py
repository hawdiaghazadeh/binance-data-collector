"""Kelly criterion risk plugin (Phase 13)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import PipelineContext
from quant_platform.core.plugin import PluginMetadata
from quant_platform.risks.kelly import check_kelly_risk, kelly_position_size

PLUGIN_METADATA = PluginMetadata(
    name="kelly_risk",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Kelly criterion position sizing with exposure cap",
    input_types=["portfolio_state", "trade_stats", "order"],
    output_types=["risk_state"],
    registry_group="platform.risks",
)


class KellyRisk:
    def __init__(
        self,
        *,
        cap: float = 0.25,
        max_exposure: float = 1.0,
    ) -> None:
        self._cap = cap
        self._max_exposure = max_exposure

    def check(self, ctx: PipelineContext, order: Any) -> bool:
        return check_kelly_risk(ctx, order, max_exposure=self._max_exposure)

    def position_size(self, ctx: PipelineContext) -> float:
        return kelly_position_size(ctx, cap=self._cap)


def factory(
    *,
    cap: float = 0.25,
    max_exposure: float = 1.0,
    config: dict | None = None,
    **kwargs,
) -> KellyRisk:
    if config:
        cap = float(config.get("cap", cap))
        max_exposure = float(config.get("max_exposure", max_exposure))
    return KellyRisk(cap=cap, max_exposure=max_exposure)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
