"""In-memory RL model registry (G37)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ModelRecord:
    model_id: str
    checkpoint_path: str
    graph_schema_hash: str
    schema_version: str
    metadata: dict[str, Any] = field(default_factory=dict)


class ModelRegistry:
    """Track deployed RL checkpoints and schema metadata."""

    def __init__(self) -> None:
        self._models: dict[str, ModelRecord] = {}

    def register(
        self,
        model_id: str,
        checkpoint_path: str | Path,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> ModelRecord:
        meta = dict(metadata or {})
        record = ModelRecord(
            model_id=model_id,
            checkpoint_path=str(checkpoint_path),
            graph_schema_hash=str(meta.get("graph_schema_hash", "")),
            schema_version=str(meta.get("schema_version", "1.0")),
            metadata=meta,
        )
        self._models[model_id] = record
        return record

    def get(self, model_id: str) -> ModelRecord:
        if model_id not in self._models:
            raise KeyError(f"model not found: {model_id}")
        return self._models[model_id]

    def list_models(self) -> list[ModelRecord]:
        return list(self._models.values())

    def remove(self, model_id: str) -> None:
        self._models.pop(model_id, None)

    def clear(self) -> None:
        self._models.clear()
