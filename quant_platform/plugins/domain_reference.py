"""Backward compatibility shim — import from quant_platform.plugins.domain."""

from quant_platform.plugins.domain import (
    DOMAIN_PLUGINS,
    DOMAIN_PLUGIN_MODULES,
    register_all_domain_plugins,
)

__all__ = ["DOMAIN_PLUGINS", "DOMAIN_PLUGIN_MODULES", "register_all_domain_plugins"]
