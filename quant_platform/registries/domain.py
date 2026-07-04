"""Domain registry singletons — Phases 4-21."""

from __future__ import annotations

from quant_platform.core.registry import BaseRegistry
from quant_platform.interfaces.domain import (
    ActionProtocol,
    BacktestingProtocol,
    BrokerProtocol,
    ConfigurationProtocol,
    EnvironmentProtocol,
    EvaluationPipelineProtocol,
    ExchangeProtocol,
    ExecutionProtocol,
    IndicatorProtocol,
    LabelProtocol,
    LiveTradingProtocol,
    MarketStructureProtocol,
    MonitoringProtocol,
    NormalizationProtocol,
    NotificationProtocol,
    ObservationProtocol,
    PaperTradingProtocol,
    PortfolioProtocol,
    ReplayBufferProtocol,
    RewardProtocol,
    RLAlgorithmProtocol,
    RiskProtocol,
    StrategyProtocol,
    TrainingPipelineProtocol,
    VisualizationProtocol,
)

NORMALIZATION_GROUP = "platform.normalizations"
INDICATOR_GROUP = "platform.indicators"
MARKET_STRUCTURE_GROUP = "platform.market_structures"
LABEL_GROUP = "platform.labels"
OBSERVATION_GROUP = "platform.observations"
REWARD_GROUP = "platform.rewards"
ACTION_GROUP = "platform.actions"
ENVIRONMENT_GROUP = "platform.environments"
STRATEGY_GROUP = "platform.strategies"
EXECUTION_GROUP = "platform.executions"
RISK_GROUP = "platform.risks"
PORTFOLIO_GROUP = "platform.portfolios"
EXCHANGE_GROUP = "platform.exchanges"
BROKER_GROUP = "platform.brokers"
REPLAY_BUFFER_GROUP = "platform.replay_buffers"
RL_ALGORITHM_GROUP = "platform.rl_algorithms"
TRAINING_PIPELINE_GROUP = "platform.training_pipelines"
EVALUATION_PIPELINE_GROUP = "platform.evaluation_pipelines"
BACKTESTING_GROUP = "platform.backtesting"
PAPER_TRADING_GROUP = "platform.paper_trading"
LIVE_TRADING_GROUP = "platform.live_trading"
VISUALIZATION_GROUP = "platform.visualizations"
NOTIFICATION_GROUP = "platform.notifications"
MONITORING_GROUP = "platform.monitoring"
CONFIGURATION_GROUP = "platform.configurations"

normalization_registry = BaseRegistry.get_instance(NORMALIZATION_GROUP)
indicator_registry = BaseRegistry.get_instance(INDICATOR_GROUP)
market_structure_registry = BaseRegistry.get_instance(MARKET_STRUCTURE_GROUP)
label_registry = BaseRegistry.get_instance(LABEL_GROUP)
observation_registry = BaseRegistry.get_instance(OBSERVATION_GROUP)
reward_registry = BaseRegistry.get_instance(REWARD_GROUP)
action_registry = BaseRegistry.get_instance(ACTION_GROUP)
environment_registry = BaseRegistry.get_instance(ENVIRONMENT_GROUP)
strategy_registry = BaseRegistry.get_instance(STRATEGY_GROUP)
execution_registry = BaseRegistry.get_instance(EXECUTION_GROUP)
risk_registry = BaseRegistry.get_instance(RISK_GROUP)
portfolio_registry = BaseRegistry.get_instance(PORTFOLIO_GROUP)
exchange_registry = BaseRegistry.get_instance(EXCHANGE_GROUP)
broker_registry = BaseRegistry.get_instance(BROKER_GROUP)
replay_buffer_registry = BaseRegistry.get_instance(REPLAY_BUFFER_GROUP)
rl_algorithm_registry = BaseRegistry.get_instance(RL_ALGORITHM_GROUP)
training_pipeline_registry = BaseRegistry.get_instance(TRAINING_PIPELINE_GROUP)
evaluation_pipeline_registry = BaseRegistry.get_instance(EVALUATION_PIPELINE_GROUP)
backtesting_registry = BaseRegistry.get_instance(BACKTESTING_GROUP)
paper_trading_registry = BaseRegistry.get_instance(PAPER_TRADING_GROUP)
live_trading_registry = BaseRegistry.get_instance(LIVE_TRADING_GROUP)
visualization_registry = BaseRegistry.get_instance(VISUALIZATION_GROUP)
notification_registry = BaseRegistry.get_instance(NOTIFICATION_GROUP)
monitoring_registry = BaseRegistry.get_instance(MONITORING_GROUP)
configuration_registry = BaseRegistry.get_instance(CONFIGURATION_GROUP)

GROUP_REGISTRY_MAP = {
    NORMALIZATION_GROUP: normalization_registry,
    INDICATOR_GROUP: indicator_registry,
    MARKET_STRUCTURE_GROUP: market_structure_registry,
    LABEL_GROUP: label_registry,
    OBSERVATION_GROUP: observation_registry,
    REWARD_GROUP: reward_registry,
    ACTION_GROUP: action_registry,
    ENVIRONMENT_GROUP: environment_registry,
    STRATEGY_GROUP: strategy_registry,
    EXECUTION_GROUP: execution_registry,
    RISK_GROUP: risk_registry,
    PORTFOLIO_GROUP: portfolio_registry,
    EXCHANGE_GROUP: exchange_registry,
    BROKER_GROUP: broker_registry,
    REPLAY_BUFFER_GROUP: replay_buffer_registry,
    RL_ALGORITHM_GROUP: rl_algorithm_registry,
    TRAINING_PIPELINE_GROUP: training_pipeline_registry,
    EVALUATION_PIPELINE_GROUP: evaluation_pipeline_registry,
    BACKTESTING_GROUP: backtesting_registry,
    PAPER_TRADING_GROUP: paper_trading_registry,
    LIVE_TRADING_GROUP: live_trading_registry,
    VISUALIZATION_GROUP: visualization_registry,
    NOTIFICATION_GROUP: notification_registry,
    MONITORING_GROUP: monitoring_registry,
    CONFIGURATION_GROUP: configuration_registry,
}
