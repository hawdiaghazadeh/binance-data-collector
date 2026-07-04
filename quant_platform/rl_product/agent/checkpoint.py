"""Model checkpoint with schema metadata (G34)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from quant_platform.rl_product.agent.network import ActorCriticModule, SplitTrunkActorCritic
from quant_platform.rl_product.observation.schema import ObservationSchema


def build_checkpoint_metadata(
    *,
    schema: ObservationSchema,
    graph_schema_hash: str = "",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    meta = {
        "schema_version": schema.schema_version,
        "obs_dim": schema.obs_dim,
        "context_dims": schema.context_dims,
        "portfolio_dims": schema.portfolio_dims,
        "reserved_dims": schema.reserved_dims,
        "price_dims": schema.price_dims,
        "block_slices": {k: [v.start, v.stop] for k, v in schema.block_slices().items()},
        "graph_schema_hash": graph_schema_hash,
    }
    if extra:
        meta.update(extra)
    return meta


def save_checkpoint(
    path: str | Path,
    model: ActorCriticModule,
    *,
    schema: ObservationSchema,
    graph_schema_hash: str = "",
    optimizer_state: dict[str, Any] | None = None,
) -> None:
    import torch

    payload = {
        "model_state": model.state_dict(),
        "metadata": build_checkpoint_metadata(schema=schema, graph_schema_hash=graph_schema_hash),
        "optimizer_state": optimizer_state,
    }
    torch.save(payload, Path(path))


def load_checkpoint(
    path: str | Path,
    *,
    config: dict[str, Any] | None = None,
    map_location: str | None = "cpu",
) -> tuple[ActorCriticModule, dict[str, Any]]:
    import torch

    from quant_platform.rl_product.agent.config import AgentConfig

    payload = torch.load(Path(path), map_location=map_location, weights_only=False)
    metadata = payload["metadata"]
    schema = ObservationSchema(
        obs_dim=int(metadata["obs_dim"]),
        context_dims=int(metadata["context_dims"]),
        portfolio_dims=int(metadata["portfolio_dims"]),
        reserved_dims=int(metadata["reserved_dims"]),
        schema_version=str(metadata["schema_version"]),
    )
    schema.validate_budget()
    agent_cfg = AgentConfig.from_config(config or {})
    core = SplitTrunkActorCritic(
        schema,
        price_trunk_hidden=agent_cfg.price_trunk_hidden,
        context_trunk_hidden=agent_cfg.context_trunk_hidden,
        portfolio_trunk_hidden=agent_cfg.portfolio_trunk_hidden,
        action_dim=agent_cfg.action_dim,
    )
    model = ActorCriticModule(core)
    model.load_state_dict(payload["model_state"])
    return model, metadata


def metadata_json(metadata: dict[str, Any]) -> str:
    return json.dumps(metadata, sort_keys=True)
