"""Phase 20 observability tests."""

from __future__ import annotations

import httpx
import pytest
import respx

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.manager import PluginManager
from quant_platform.observability.monitoring import MetricsRegistry
from quant_platform.observability.notification import send_slack_message
from quant_platform.observability.pipeline import ObservabilityPipelineBuilder, register_observability_plugins
from quant_platform.observability.visualization import render_equity_curve


class TestObservabilityCompute:
    def test_render_equity_curve(self):
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="equity_curve", payload=[10_000.0, 10_100.0, 10_250.0]))
        chart = render_equity_curve(ctx)
        assert chart["type"] == "equity_curve"
        assert chart["series"][0]["values"][-1] == 10_250.0
        assert chart["grafana_panel"]["type"] == "timeseries"

    def test_metrics_registry_prometheus_export(self):
        registry = MetricsRegistry()
        registry.record("equity.latest", 10250.0, {"symbol": "BTCUSDT"})
        exported = registry.export_prometheus()
        assert 'equity_latest{symbol="BTCUSDT"} 10250.0' in exported

    def test_send_slack_without_webhook(self):
        assert send_slack_message("hello") is True

    @respx.mock
    def test_send_slack_with_webhook(self):
        respx.post("https://hooks.slack.test/abc").mock(return_value=httpx.Response(200, json={"ok": True}))
        assert send_slack_message("trade filled", webhook_url="https://hooks.slack.test/abc") is True


class TestObservabilityRegistry:
    def test_equity_curve_plugin(self):
        manager = PluginManager()
        register_observability_plugins(manager)
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="equity_curve", payload=[100.0, 110.0]))
        viz = manager.get("platform.visualizations", "equity_curve")
        chart = viz.render(ctx)
        assert chart["type"] == "equity_curve"
        assert "visualization" in ctx.keys()

    def test_slack_notifier_plugin(self):
        manager = PluginManager()
        register_observability_plugins(manager)
        notifier = manager.get("platform.notifications", "slack_notifier")
        assert notifier.send("pipeline started") is True

    def test_structlog_monitoring_plugin(self):
        manager = PluginManager()
        register_observability_plugins(manager)
        monitor = manager.get("platform.monitoring", "structlog_monitoring")
        monitor.record_metric("latency_ms", 12.5, tags={"service": "paper"})
        assert len(monitor.snapshot()) == 1

    def test_prometheus_metrics_plugin(self):
        manager = PluginManager()
        register_observability_plugins(manager)
        monitor = manager.get("platform.monitoring", "prometheus_metrics")
        monitor.record_metric("trades.count", 3.0)
        assert "trades_count 3.0" in monitor.export()

    def test_observability_pipeline_builder(self):
        manager = PluginManager()
        register_observability_plugins(manager)
        builder = ObservabilityPipelineBuilder(manager)
        ctx = PipelineContext()
        ctx.emit(DataEnvelope(type_key="equity_curve", payload=[10_000.0, 10_050.0]))
        ctx.emit(DataEnvelope(type_key="step_pnl", payload=50.0))
        result = builder.emit(ctx, message="session complete")
        assert result["notification_sent"] is True
        assert result["metrics_recorded"] >= 2
        assert ctx.require("observability_result").payload == result
        assert ctx.require("visualization").payload["type"] == "equity_curve"
