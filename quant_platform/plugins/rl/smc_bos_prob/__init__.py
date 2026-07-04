"""SMC BOS probability hint plugin."""

from __future__ import annotations

from quant_platform.plugins.rl._hint_plugin import build_hint_plugin
from quant_platform.rl_product.perception.smc import compute_bos_prob

PLUGIN_METADATA, factory = build_hint_plugin(
    name="smc_bos_prob",
    family="smc",
    hint_name="bos_p",
    description="Probabilistic BOS hint from visible swing structure",
    compute=compute_bos_prob,
    default_options={"swing_lookback": 2},
)

__all__ = ["PLUGIN_METADATA", "factory"]
