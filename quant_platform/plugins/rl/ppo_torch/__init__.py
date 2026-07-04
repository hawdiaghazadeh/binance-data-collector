"""PyTorch PPO plugin — split-trunk actor-critic (G34)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.plugin import PluginMetadata
from quant_platform.rl_product.agent.checkpoint import load_checkpoint, save_checkpoint
from quant_platform.rl_product.agent.config import AgentConfig
from quant_platform.rl_product.agent.network import ActorCriticModule, SplitTrunkActorCritic
from quant_platform.rl_product.agent.ppo import PPOTrainer
from quant_platform.rl_product.graph import RLProductGraph
from quant_platform.rl_product.observation.schema import ObservationSchema
from quant_platform.rl_product.registry import RL_GROUP

PLUGIN_METADATA = PluginMetadata(
    name="ppo_torch",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Split-trunk PPO with GAE, advantage norm, and schema-tagged checkpoints",
    input_types=["rollout_batch", "training_config"],
    output_types=["training_metrics", "policy_checkpoint"],
    registry_group=RL_GROUP,
)


class PpoTorchPlugin:
    def __init__(
        self,
        *,
        trainer: PPOTrainer | None = None,
        schema: ObservationSchema | None = None,
        graph: RLProductGraph | None = None,
    ) -> None:
        self._trainer = trainer
        self._schema = schema
        self._graph = graph

    @property
    def trainer(self) -> PPOTrainer | None:
        return self._trainer

    def build_trainer(self, config: dict[str, Any]) -> PPOTrainer:
        graph = self._graph or RLProductGraph.compile(config)
        schema = self._schema or ObservationSchema.from_config(config)
        schema.validate_budget()
        self._graph = graph
        self._schema = schema
        self._trainer = PPOTrainer.from_schema(schema, config)
        return self._trainer

    def save(self, path: str, *, config: dict[str, Any] | None = None) -> None:
        if self._trainer is None or self._schema is None:
            raise RuntimeError("trainer not initialized")
        graph_hash = self._graph.schema_hash if self._graph else ""
        save_checkpoint(
            path,
            self._trainer.model,
            schema=self._schema,
            graph_schema_hash=graph_hash,
        )

    def load(self, path: str, *, config: dict[str, Any] | None = None) -> PPOTrainer:
        model, metadata = load_checkpoint(path, config=config)
        cfg = AgentConfig.from_config(config or {})
        self._schema = ObservationSchema(
            obs_dim=int(metadata["obs_dim"]),
            context_dims=int(metadata["context_dims"]),
            portfolio_dims=int(metadata["portfolio_dims"]),
            reserved_dims=int(metadata["reserved_dims"]),
            schema_version=str(metadata["schema_version"]),
        )
        self._trainer = PPOTrainer(model, cfg)
        return self._trainer


def factory(*, config: dict | None = None, **kwargs) -> PpoTorchPlugin:
    plugin = PpoTorchPlugin()
    if config:
        plugin.build_trainer(config)
    return plugin


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
