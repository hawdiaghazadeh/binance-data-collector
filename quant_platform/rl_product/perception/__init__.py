"""Perception hints — RTM / SMC / ICT (G31)."""

from quant_platform.rl_product.perception.compressor import PerceptionCompressor
from quant_platform.rl_product.perception.gate import FeatureGate, GateConfig
from quant_platform.rl_product.perception.pipeline import PerceptionPipeline

__all__ = [
    "FeatureGate",
    "GateConfig",
    "PerceptionCompressor",
    "PerceptionPipeline",
]
