"""Feature gate plugin — master and per-family context masking."""

from __future__ import annotations

from quant_platform.core.plugin import PluginMetadata
from quant_platform.rl_product.perception.gate import FeatureGate, GateConfig
from quant_platform.rl_product.registry import RL_GROUP

PLUGIN_METADATA = PluginMetadata(
    name="feature_gate",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Apply master_gate and per-family gates to context vector",
    input_types=["context_vector"],
    output_types=["gated_context"],
    registry_group=RL_GROUP,
)


class FeatureGatePlugin:
    def __init__(self, *, gate: FeatureGate | None = None) -> None:
        self._gate = gate or FeatureGate()

    @property
    def gate(self) -> FeatureGate:
        return self._gate

    def apply(self, context: list[float], config: dict | None = None, *, context_dims: int | None = None) -> list[float]:
        if config:
            self._gate.update(GateConfig.from_config(config))
        return self._gate.apply(context, context_dims=context_dims)


def factory(*, config: dict | None = None, **kwargs) -> FeatureGatePlugin:
    gate = FeatureGate(GateConfig.from_config(config or {}))
    return FeatureGatePlugin(gate=gate)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
