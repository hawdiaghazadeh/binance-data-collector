"""Perception compressor plugin — merges hints into context vector."""

from __future__ import annotations

from typing import Any, Sequence

from quant_platform.core.plugin import PluginMetadata
from quant_platform.rl_product.perception.compressor import PerceptionCompressor
from quant_platform.rl_product.registry import RL_GROUP
from services.shared.models import KlineRow

PLUGIN_METADATA = PluginMetadata(
    name="perception_compressor",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Compress perception hints into bounded context vector (16-32 dims)",
    input_types=["perception_hints", "klines"],
    output_types=["context_vector"],
    registry_group=RL_GROUP,
)


class PerceptionCompressorPlugin:
    def __init__(self, *, context_dims: int = 16) -> None:
        self._compressor = PerceptionCompressor(context_dims=context_dims)

    @property
    def compressor(self) -> PerceptionCompressor:
        return self._compressor

    def compress(self, bars: Sequence[KlineRow], hints: dict[str, float]) -> list[float]:
        return self._compressor.compress(bars, hints)


def factory(*, context_dims: int = 16, config: dict | None = None, **kwargs) -> PerceptionCompressorPlugin:
    if config:
        observation = config.get("observation", config)
        context_dims = int(observation.get("context_dims", context_dims))
    return PerceptionCompressorPlugin(context_dims=context_dims)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
