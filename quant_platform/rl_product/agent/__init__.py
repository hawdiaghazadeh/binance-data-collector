"""RL product agent layer (G34)."""

from quant_platform.rl_product.agent.checkpoint import load_checkpoint, save_checkpoint
from quant_platform.rl_product.agent.config import AgentConfig
from quant_platform.rl_product.agent.network import ActorCriticModule, SplitTrunkActorCritic
from quant_platform.rl_product.agent.ppo import PPOTrainer

__all__ = [
    "ActorCriticModule",
    "AgentConfig",
    "PPOTrainer",
    "SplitTrunkActorCritic",
    "load_checkpoint",
    "save_checkpoint",
]
