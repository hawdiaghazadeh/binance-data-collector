"""Reference domain plugin: paper_broker."""

from __future__ import annotations

from typing import Any

from quant_platform.plugins.domain._helpers import attach_factory_metadata, reference_meta

PLUGIN_METADATA = reference_meta("paper_broker", "platform.brokers")


class PaperBroker:

    def submit_order(self, order: Any) -> dict:
        return {"order_id": "paper-1", "status": "submitted"}

    def cancel_order(self, order_id: str) -> bool:
        return True


def factory(**kwargs) -> PaperBroker:
    return PaperBroker()


attach_factory_metadata(factory, PLUGIN_METADATA)
