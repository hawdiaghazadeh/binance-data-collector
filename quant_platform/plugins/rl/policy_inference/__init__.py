"""Policy inference plugin (G37)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from quant_platform.core.plugin import PluginMetadata
from quant_platform.rl_product.inference.policy_inference import PolicyInferenceEngine
from quant_platform.rl_product.registry import RL_GROUP


PLUGIN_METADATA = PluginMetadata(
    name="policy_inference",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Load RL checkpoint with graph schema hash validation",
    input_types=["checkpoint_path", "training_config"],
    output_types=["policy_engine"],
    registry_group=RL_GROUP,
)


class PolicyInferencePlugin:
    def load(
        self,
        checkpoint_path: str | Path,
        config: dict[str, Any],
        *,
        strict_hash: bool = True,
    ) -> PolicyInferenceEngine:
        return PolicyInferenceEngine.from_checkpoint(
            checkpoint_path,
            config,
            strict_hash=strict_hash,
        )


def factory(**kwargs) -> PolicyInferencePlugin:
    return PolicyInferencePlugin()


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
