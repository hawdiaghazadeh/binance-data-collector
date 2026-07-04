"""Grouped observability pipeline — Phase 20."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.execution_graph import CompiledExecutionGraph, ExecutionStep
from quant_platform.core.manager import PluginManager
from quant_platform.observability.events import extract_metrics_from_context
from quant_platform.registries.domain import (
    MONITORING_GROUP,
    NOTIFICATION_GROUP,
    VISUALIZATION_GROUP,
)


class ObservabilityPipelineBuilder:
    """Emit visualization, notification, and metrics from one pipeline context."""

    def __init__(self, manager: PluginManager) -> None:
        self._manager = manager

    def emit(
        self,
        ctx: PipelineContext,
        *,
        message: str | None = None,
        channel: str = "default",
        visualization_name: str = "equity_curve",
        notification_name: str = "slack_notifier",
        monitoring_name: str = "structlog_monitoring",
    ) -> dict[str, Any]:
        visualization = self._manager.get(VISUALIZATION_GROUP, visualization_name)
        chart = visualization.render(ctx)
        ctx.emit(DataEnvelope(type_key="visualization", payload=chart))

        sent = True
        if message:
            notifier = self._manager.get(NOTIFICATION_GROUP, notification_name)
            sent = bool(notifier.send(message, channel=channel))

        monitor = self._manager.get(MONITORING_GROUP, monitoring_name)
        for name, value, tags in extract_metrics_from_context(ctx):
            monitor.record_metric(name, value, tags=tags or None)

        result = {
            "visualization": chart,
            "notification_sent": sent,
            "metrics_recorded": len(extract_metrics_from_context(ctx)),
        }
        ctx.emit(DataEnvelope(type_key="observability_result", payload=result))
        return result

    def build_graph(
        self,
        *,
        visualization_name: str = "equity_curve",
        notification_name: str = "slack_notifier",
        monitoring_name: str = "structlog_monitoring",
    ) -> CompiledExecutionGraph:
        def handler(ctx: PipelineContext) -> None:
            request = ctx.require("observability_request").payload
            self.emit(
                ctx,
                message=request.get("message"),
                channel=str(request.get("channel", "default")),
                visualization_name=visualization_name,
                notification_name=notification_name,
                monitoring_name=monitoring_name,
            )

        return CompiledExecutionGraph(
            (
                ExecutionStep(
                    plugin_name="observability",
                    handler=handler,
                    registry_group=MONITORING_GROUP,
                ),
            )
        )


def register_visualization_plugins(manager: PluginManager) -> None:
    from quant_platform.plugins.domain.equity_curve import PLUGIN_METADATA as EQUITY_META
    from quant_platform.plugins.domain.equity_curve import factory as equity_factory

    reg = manager.registry(VISUALIZATION_GROUP)
    if EQUITY_META.name not in {m.name for m in reg.list_plugins()}:
        reg.register(EQUITY_META, equity_factory)


def register_notification_plugins(manager: PluginManager) -> None:
    from quant_platform.plugins.domain.slack_notifier import PLUGIN_METADATA as SLACK_META
    from quant_platform.plugins.domain.slack_notifier import factory as slack_factory

    reg = manager.registry(NOTIFICATION_GROUP)
    if SLACK_META.name not in {m.name for m in reg.list_plugins()}:
        reg.register(SLACK_META, slack_factory)


def register_monitoring_plugins(manager: PluginManager) -> None:
    from quant_platform.plugins.domain.prometheus_metrics import PLUGIN_METADATA as PROM_META
    from quant_platform.plugins.domain.prometheus_metrics import factory as prom_factory
    from quant_platform.plugins.domain.structlog_monitoring import PLUGIN_METADATA as STRUCT_META
    from quant_platform.plugins.domain.structlog_monitoring import factory as struct_factory

    reg = manager.registry(MONITORING_GROUP)
    for meta, factory in [(STRUCT_META, struct_factory), (PROM_META, prom_factory)]:
        if meta.name not in {m.name for m in reg.list_plugins()}:
            reg.register(meta, factory)


def register_observability_plugins(manager: PluginManager) -> None:
    register_visualization_plugins(manager)
    register_notification_plugins(manager)
    register_monitoring_plugins(manager)
