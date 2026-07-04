"""RTM liquidity sweep probability hint plugin."""

from __future__ import annotations

from quant_platform.plugins.rl._hint_plugin import build_hint_plugin
from quant_platform.rl_product.perception.rtm import compute_sweep_prob

PLUGIN_METADATA, factory = build_hint_plugin(
    name="rtm_sweep_prob",
    family="rtm",
    hint_name="sweep_p",
    description="Liquidity sweep probability from wick rejection",
    compute=compute_sweep_prob,
    default_options={"lookback": 10},
)

__all__ = ["PLUGIN_METADATA", "factory"]
