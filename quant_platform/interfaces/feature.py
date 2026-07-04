"""Feature protocol (Phase 3)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from quant_platform.core.context import PipelineContext


@runtime_checkable
class FeatureProtocol(Protocol):
    def compute(self, ctx: PipelineContext) -> None: ...
