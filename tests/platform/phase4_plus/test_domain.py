"""Phase 4+ domain registry tests."""

from __future__ import annotations

from quant_platform.core.manager import PluginManager
from quant_platform.plugins.domain_reference import register_all_domain_plugins


class TestDomainRegistries:
    def test_register_all_domain_plugins(self):
        manager = PluginManager()
        count = register_all_domain_plugins(manager)
        assert count >= 20

    def test_normalization_plugin(self):
        manager = PluginManager()
        register_all_domain_plugins(manager)
        normalizer = manager.get("platform.normalizations", "symbol_normalizer")
        assert normalizer is not None

    def test_rl_core_plugins(self):
        manager = PluginManager()
        register_all_domain_plugins(manager)
        buffer = manager.get("platform.replay_buffers", "uniform_buffer")
        algo = manager.get("platform.rl_algorithms", "ppo")
        train = manager.get("platform.training_pipelines", "standard_rl_train")
        assert buffer.sample(1) == []
        assert algo.train_step([])["loss"] == 0.0
        assert train.run({})["status"] == "completed"

    def test_observability_plugins(self):
        manager = PluginManager()
        register_all_domain_plugins(manager)
        notifier = manager.get("platform.notifications", "slack_notifier")
        monitor = manager.get("platform.monitoring", "structlog_monitoring")
        viz = manager.get("platform.visualizations", "equity_curve")
        from quant_platform.core.context import PipelineContext

        assert notifier.send("test") is True
        monitor.record_metric("latency", 1.0)
        assert viz.render(PipelineContext()) == {"type": "equity_curve"}
