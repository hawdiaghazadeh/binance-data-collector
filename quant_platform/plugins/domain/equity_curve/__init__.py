"""Reference domain plugin: equity_curve."""

from __future__ import annotations

from quant_platform.core.context import PipelineContext

from quant_platform.plugins.domain._helpers import attach_factory_metadata, reference_meta

PLUGIN_METADATA = reference_meta("equity_curve", "platform.visualizations")


class EquityCurveViz:

    def render(self, ctx: PipelineContext) -> dict:
        return {"type": "equity_curve"}


def factory(**kwargs) -> EquityCurveViz:
    return EquityCurveViz()


attach_factory_metadata(factory, PLUGIN_METADATA)
