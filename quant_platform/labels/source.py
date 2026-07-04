"""Resolve close series for label plugins (Phase 7)."""

from __future__ import annotations

from quant_platform.core.context import PipelineContext
from quant_platform.indicators.source import resolve_closes


def resolve_label_closes(ctx: PipelineContext) -> list[float]:
    return resolve_closes(ctx)
