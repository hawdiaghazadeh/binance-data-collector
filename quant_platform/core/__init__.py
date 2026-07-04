"""Platform core exports."""

from quant_platform.core.config import ConfigValidationError, validate_plugin_config
from quant_platform.core.discovery import register
from quant_platform.core.manager import PluginManager, PluginsConfig
from quant_platform.core.plugin import (
    DisableReason,
    PluginDependency,
    PluginLifecycle,
    PluginMetadata,
    PluginRecord,
    PluginStatus,
)
from quant_platform.core.registry import BaseRegistry, PluginUnavailableError, RegistryError

__all__ = [
    "BaseRegistry",
    "ConfigValidationError",
    "DisableReason",
    "PluginDependency",
    "PluginLifecycle",
    "PluginManager",
    "PluginMetadata",
    "PluginRecord",
    "PluginStatus",
    "PluginUnavailableError",
    "PluginsConfig",
    "RegistryError",
    "register",
    "validate_plugin_config",
]
