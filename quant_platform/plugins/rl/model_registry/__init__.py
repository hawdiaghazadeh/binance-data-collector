"""RL model registry plugin (G37)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from quant_platform.core.plugin import PluginMetadata
from quant_platform.rl_product.inference.model_registry import ModelRegistry
from quant_platform.rl_product.registry import RL_GROUP


PLUGIN_METADATA = PluginMetadata(
    name="model_registry",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="In-memory registry for deployed RL checkpoints",
    input_types=["checkpoint_path", "model_id"],
    output_types=["model_record"],
    registry_group=RL_GROUP,
)


class ModelRegistryPlugin:
    def __init__(self, registry: ModelRegistry | None = None) -> None:
        self._registry = registry or ModelRegistry()

    @property
    def registry(self) -> ModelRegistry:
        return self._registry

    def register(self, model_id: str, checkpoint_path: str | Path, *, metadata: dict[str, Any] | None = None):
        return self._registry.register(model_id, checkpoint_path, metadata=metadata)

    def get(self, model_id: str):
        return self._registry.get(model_id)

    def list_models(self):
        return self._registry.list_models()


def factory(**kwargs) -> ModelRegistryPlugin:
    return ModelRegistryPlugin()


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
