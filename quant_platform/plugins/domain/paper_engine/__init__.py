"""Reference domain plugin: paper_engine."""

from __future__ import annotations

from quant_platform.plugins.domain._helpers import attach_factory_metadata, reference_meta

PLUGIN_METADATA = reference_meta("paper_engine", "platform.paper_trading")


class PaperTradingEngine:

    def start(self) -> None:
        pass

    def stop(self) -> dict:
        return {"status": "stopped"}


def factory(**kwargs) -> PaperTradingEngine:
    return PaperTradingEngine()


attach_factory_metadata(factory, PLUGIN_METADATA)
