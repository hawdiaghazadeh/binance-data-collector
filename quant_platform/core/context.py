"""Runtime data bus — PipelineContext and DataEnvelope (Phase 2B)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


class EnvelopeNotFoundError(KeyError):
    """Raised when a required envelope type is missing."""


@dataclass(frozen=True)
class DataEnvelope:
    type_key: str
    payload: Any
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class PipelineContext:
    """Per-run data bus for plugin communication."""

    def __init__(self, run_id: str | None = None) -> None:
        self.run_id = run_id or datetime.now(timezone.utc).isoformat()
        self._envelopes: dict[str, DataEnvelope] = {}

    def emit(self, envelope: DataEnvelope) -> None:
        self._envelopes[envelope.type_key] = envelope

    def require(self, type_key: str) -> DataEnvelope:
        if type_key not in self._envelopes:
            raise EnvelopeNotFoundError(f"Required envelope '{type_key}' not found")
        return self._envelopes[type_key]

    def optional(self, type_key: str) -> DataEnvelope | None:
        return self._envelopes.get(type_key)

    def keys(self) -> list[str]:
        return list(self._envelopes.keys())
