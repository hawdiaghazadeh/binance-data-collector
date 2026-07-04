"""Reference domain plugin: structlog_monitoring."""

from __future__ import annotations

from quant_platform.plugins.domain._helpers import attach_factory_metadata, reference_meta

PLUGIN_METADATA = reference_meta("structlog_monitoring", "platform.monitoring")


class StructlogMonitoring:

    def record_metric(self, name: str, value: float, tags: dict | None = None) -> None:
        pass


def factory(**kwargs) -> StructlogMonitoring:
    return StructlogMonitoring()


attach_factory_metadata(factory, PLUGIN_METADATA)
