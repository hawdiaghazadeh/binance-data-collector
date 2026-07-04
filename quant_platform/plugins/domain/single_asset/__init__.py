"""Reference domain plugin: single_asset."""

from __future__ import annotations

from typing import Any
from quant_platform.core.context import PipelineContext

from quant_platform.plugins.domain._helpers import attach_factory_metadata, reference_meta

PLUGIN_METADATA = reference_meta("single_asset", "platform.portfolios")


class SingleAssetPortfolio:

    def __init__(self) -> None:
        self._positions: dict[str, Any] = {}

    def update(self, ctx: PipelineContext) -> None:
        pass

    def positions(self) -> dict[str, Any]:
        return dict(self._positions)


def factory(**kwargs) -> SingleAssetPortfolio:
    return SingleAssetPortfolio()


attach_factory_metadata(factory, PLUGIN_METADATA)
