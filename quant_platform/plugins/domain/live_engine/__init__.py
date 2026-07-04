"""Reference domain plugin: live_engine."""

from __future__ import annotations

from quant_platform.plugins.domain._helpers import attach_factory_metadata, reference_meta

PLUGIN_METADATA = reference_meta("live_engine", "platform.live_trading")


class LiveTradingEngine:

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass


def factory(**kwargs) -> LiveTradingEngine:
    return LiveTradingEngine()


attach_factory_metadata(factory, PLUGIN_METADATA)
