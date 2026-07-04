"""Composable observation builders."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.interfaces.domain import ObservationProtocol


class CompositeObservation:
    """Merge multiple observation spaces into one payload."""

    def __init__(self, observations: list[tuple[ObservationProtocol, str]]) -> None:
        self._observations = observations

    def build(self, ctx: PipelineContext) -> dict[str, Any]:
        merged: dict[str, Any] = {}
        for builder, key in self._observations:
            part = builder.build(ctx)
            merged[key] = part
        ctx.emit(DataEnvelope(type_key="observation", payload=merged))
        return merged
