"""Reference domain plugin: event_driven."""

from __future__ import annotations

from typing import Any

from quant_platform.plugins.domain._helpers import attach_factory_metadata, reference_meta

PLUGIN_METADATA = reference_meta("event_driven", "platform.backtesting")


class EventDrivenBacktest:

    def run(self, strategy: Any, data: Any) -> dict:
        return {"pnl": 0.0, "trades": 0}


def factory(**kwargs) -> EventDrivenBacktest:
    return EventDrivenBacktest()


attach_factory_metadata(factory, PLUGIN_METADATA)
