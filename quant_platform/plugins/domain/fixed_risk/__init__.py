"""Reference domain plugin: fixed_risk."""

from __future__ import annotations

from typing import Any
from quant_platform.core.context import PipelineContext

from quant_platform.plugins.domain._helpers import attach_factory_metadata, reference_meta

PLUGIN_METADATA = reference_meta("fixed_risk", "platform.risks")


class FixedRisk:

    def check(self, ctx: PipelineContext, order: Any) -> bool:
        return True

    def position_size(self, ctx: PipelineContext) -> float:
        return 0.01


def factory(**kwargs) -> FixedRisk:
    return FixedRisk()


attach_factory_metadata(factory, PLUGIN_METADATA)
