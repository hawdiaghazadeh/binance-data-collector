"""Prometheus metrics plugin (Phase 20)."""

from __future__ import annotations

from quant_platform.core.plugin import PluginMetadata
from quant_platform.observability.monitoring import MetricsRegistry

PLUGIN_METADATA = PluginMetadata(
    name="prometheus_metrics",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="In-memory metrics registry with Prometheus text export",
    input_types=["metrics"],
    output_types=["prometheus_metrics"],
    registry_group="platform.monitoring",
)


class PrometheusMetrics:
    def __init__(self, registry: MetricsRegistry | None = None) -> None:
        self._registry = registry or MetricsRegistry()

    def record_metric(self, name: str, value: float, tags: dict | None = None) -> None:
        tag_map = {str(key): str(val) for key, val in (tags or {}).items()}
        self._registry.record(name, value, tag_map)

    def export(self) -> str:
        return self._registry.export_prometheus()

    def snapshot(self) -> list[tuple[str, float, dict[str, str]]]:
        return self._registry.snapshot()


def factory(**kwargs) -> PrometheusMetrics:
    return PrometheusMetrics()


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
