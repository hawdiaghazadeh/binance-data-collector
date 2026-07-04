"""Portfolio observation plugin (Phase 8)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.plugin import PluginMetadata
from quant_platform.observations.portfolio import build_portfolio_observation

PLUGIN_METADATA = PluginMetadata(
    name="portfolio_observation",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Portfolio state observation from portfolio_state envelope",
    input_types=["portfolio_state"],
    output_types=["portfolio_observation"],
    registry_group="platform.observations",
)


class PortfolioObservation:
    def build(self, ctx: PipelineContext) -> dict[str, Any]:
        observation = build_portfolio_observation(ctx)
        ctx.emit(DataEnvelope(type_key="portfolio_observation", payload=observation))
        return observation


def factory(**kwargs) -> PortfolioObservation:
    return PortfolioObservation()


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
