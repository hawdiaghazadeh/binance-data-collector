"""SMC FVG fill probability hint plugin."""

from __future__ import annotations

from quant_platform.plugins.rl._hint_plugin import build_hint_plugin
from quant_platform.rl_product.perception.smc import compute_fvg_fill_prob

PLUGIN_METADATA, factory = build_hint_plugin(
    name="smc_fvg_fill_prob",
    family="smc",
    hint_name="fvg_fill_p",
    description="Fair value gap fill probability from visible bars",
    compute=compute_fvg_fill_prob,
)

__all__ = ["PLUGIN_METADATA", "factory"]
