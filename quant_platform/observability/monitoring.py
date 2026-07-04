"""Monitoring and metrics helpers (Phase 20)."""

from __future__ import annotations

from typing import Any

import structlog


class MetricsRegistry:
    def __init__(self) -> None:
        self._records: list[tuple[str, float, dict[str, str]]] = []

    def record(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        self._records.append((name, value, dict(tags or {})))

    def snapshot(self) -> list[tuple[str, float, dict[str, str]]]:
        return list(self._records)

    def export_prometheus(self) -> str:
        lines: list[str] = []
        for name, value, tags in self._records:
            safe_name = name.replace(".", "_")
            if tags:
                label_parts = ",".join(f'{key}="{val}"' for key, val in sorted(tags.items()))
                lines.append(f"{safe_name}{{{label_parts}}} {value}")
            else:
                lines.append(f"{safe_name} {value}")
        return "\n".join(lines)


def record_structlog_metric(
    registry: MetricsRegistry,
    name: str,
    value: float,
    tags: dict[str, str] | None = None,
) -> None:
    registry.record(name, value, tags)
    logger = structlog.get_logger("quant_platform.monitoring")
    logger.info("metric_recorded", metric=name, value=value, tags=tags or {})
