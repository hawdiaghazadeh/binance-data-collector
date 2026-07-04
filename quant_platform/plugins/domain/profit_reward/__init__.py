"""Reference domain plugin: profit_reward."""

from __future__ import annotations

from quant_platform.core.context import PipelineContext

from quant_platform.plugins.domain._helpers import attach_factory_metadata, reference_meta

PLUGIN_METADATA = reference_meta("profit_reward", "platform.rewards")


class ProfitReward:

    def calculate(self, ctx: PipelineContext) -> float:
        pnl = ctx.optional("pnl")
        return float(pnl.payload) if pnl else 0.0


def factory(**kwargs) -> ProfitReward:
    return ProfitReward()


attach_factory_metadata(factory, PLUGIN_METADATA)
