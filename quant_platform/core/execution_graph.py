"""Compiled execution graph for zero-lookup runtime (Phase 2B)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from quant_platform.core.context import PipelineContext


@dataclass(frozen=True)
class ExecutionStep:
    plugin_name: str
    handler: Callable[[PipelineContext], None]
    registry_group: str = ""


class CompiledExecutionGraph:
    """Frozen execution plan — no registry access at runtime."""

    def __init__(self, steps: tuple[ExecutionStep, ...]) -> None:
        self._steps = steps

    @property
    def steps(self) -> tuple[ExecutionStep, ...]:
        return self._steps

    def execute(self, ctx: PipelineContext) -> None:
        for step in self._steps:
            step.handler(ctx)

    @classmethod
    def from_handlers(
        cls,
        handlers: list[tuple[str, Callable[[PipelineContext], None], str]],
    ) -> CompiledExecutionGraph:
        steps = tuple(
            ExecutionStep(plugin_name=name, handler=handler, registry_group=group)
            for name, handler, group in handlers
        )
        return cls(steps)

    def __len__(self) -> int:
        return len(self._steps)
