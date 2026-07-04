"""Price-action-first observation plugin (G32)."""

from __future__ import annotations

from typing import Any, Sequence

from quant_platform.core.plugin import PluginMetadata
from quant_platform.rl_product.observation.builder import PriceActionObservationBuilder
from quant_platform.rl_product.observation.schema import ObservationSchema
from quant_platform.rl_product.observation.vector import ObservationVector
from quant_platform.rl_product.registry import RL_GROUP
from services.shared.models import KlineRow

PLUGIN_METADATA = PluginMetadata(
    name="price_action_observation",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Price-action-first observation vector with gated context block",
    input_types=["klines", "portfolio_state"],
    output_types=["observation_vector"],
    registry_group=RL_GROUP,
)


class PriceActionObservationPlugin:
    def __init__(self, builder: PriceActionObservationBuilder | None = None) -> None:
        self._builder = builder

    @property
    def builder(self) -> PriceActionObservationBuilder | None:
        return self._builder

    def build(
        self,
        bars: Sequence[KlineRow],
        t: int,
        *,
        portfolio: dict[str, Any] | None = None,
        config: dict | None = None,
    ) -> ObservationVector:
        if self._builder is None:
            cfg = config or {}
            self._builder = PriceActionObservationBuilder.from_config(cfg)
        return self._builder.build(bars, t, portfolio=portfolio, config=config)


def factory(*, config: dict | None = None, **kwargs) -> PriceActionObservationPlugin:
    builder = PriceActionObservationBuilder.from_config(config or {}) if config else None
    return PriceActionObservationPlugin(builder=builder)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
