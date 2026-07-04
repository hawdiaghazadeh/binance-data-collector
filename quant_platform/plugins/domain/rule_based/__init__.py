"""Reference domain plugin: rule_based."""

from __future__ import annotations

from typing import Any
from quant_platform.core.context import PipelineContext

from quant_platform.plugins.domain._helpers import attach_factory_metadata, reference_meta

PLUGIN_METADATA = reference_meta("rule_based", "platform.strategies")


class RuleBasedStrategy:

    def on_bar(self, ctx: PipelineContext) -> None:
        pass

    def signals(self, ctx: PipelineContext) -> list[Any]:
        return []


def factory(**kwargs) -> RuleBasedStrategy:
    return RuleBasedStrategy()


attach_factory_metadata(factory, PLUGIN_METADATA)
