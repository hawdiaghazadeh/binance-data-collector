"""Reference domain plugins split by registry group (Phases 4-21)."""

from __future__ import annotations

from typing import Any, Callable

from quant_platform.core.manager import PluginManager
from quant_platform.core.plugin import PluginMetadata
from . import (
    binance_exchange,
    bos_choch,
    candle_observation,
    direction_label,
    discrete_action,
    drawdown_penalty,
    ema_indicator,
    equity_curve,
    event_driven,
    fixed_risk,
    fvg,
    live_engine,
    macd_indicator,
    order_blocks,
    paper_broker,
    paper_engine,
    portfolio_observation,
    ppo,
    profit_reward,
    regime_label,
    risk_observation,
    rule_based,
    rsi_indicator,
    schema_config,
    sharpe_reward,
    simulation_execution,
    single_asset,
    slack_notifier,
    spot_env,
    standard_rl_train,
    structlog_monitoring,
    symbol_normalizer,
    uniform_buffer,
    walk_forward,
    z_score,
)
from quant_platform.registries.domain import GROUP_REGISTRY_MAP

DOMAIN_PLUGIN_MODULES: list[tuple[str, Any]] = [
    ("platform.normalizations", symbol_normalizer),
    ("platform.normalizations", z_score),
    ("platform.indicators", ema_indicator),
    ("platform.indicators", rsi_indicator),
    ("platform.indicators", macd_indicator),
    ("platform.market_structures", bos_choch),
    ("platform.market_structures", fvg),
    ("platform.market_structures", order_blocks),
    ("platform.labels", direction_label),
    ("platform.labels", regime_label),
    ("platform.observations", candle_observation),
    ("platform.observations", portfolio_observation),
    ("platform.observations", risk_observation),
    ("platform.rewards", profit_reward),
    ("platform.rewards", sharpe_reward),
    ("platform.rewards", drawdown_penalty),
    ("platform.actions", discrete_action),
    ("platform.environments", spot_env),
    ("platform.strategies", rule_based),
    ("platform.executions", simulation_execution),
    ("platform.risks", fixed_risk),
    ("platform.portfolios", single_asset),
    ("platform.exchanges", binance_exchange),
    ("platform.brokers", paper_broker),
    ("platform.replay_buffers", uniform_buffer),
    ("platform.rl_algorithms", ppo),
    ("platform.training_pipelines", standard_rl_train),
    ("platform.evaluation_pipelines", walk_forward),
    ("platform.backtesting", event_driven),
    ("platform.paper_trading", paper_engine),
    ("platform.live_trading", live_engine),
    ("platform.visualizations", equity_curve),
    ("platform.notifications", slack_notifier),
    ("platform.monitoring", structlog_monitoring),
    ("platform.configurations", schema_config),
]

DOMAIN_PLUGINS: list[tuple[str, PluginMetadata, Callable[..., Any]]] = [
    (group, module.factory.PLUGIN_METADATA, module.factory)
    for group, module in DOMAIN_PLUGIN_MODULES
]


def register_all_domain_plugins(manager: PluginManager) -> int:
    count = 0
    domain_groups = {group for group, _ in DOMAIN_PLUGIN_MODULES}
    for group in domain_groups:
        count += manager.discover(group, scan_packages=[])

    for group, meta, factory in DOMAIN_PLUGINS:
        reg = GROUP_REGISTRY_MAP.get(group) or manager.registry(group)
        if meta.name not in {m.name for m in reg.list_plugins()}:
            reg.register(meta, factory)
            count += 1
    return count
