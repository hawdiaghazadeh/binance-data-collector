"""Marketplace plugin management — Phase 22."""

from quant_platform.marketplace.cli import build_service, main
from quant_platform.marketplace.discovery import (
    discover_entry_points_from_manifest,
    register_plugins_from_manifest,
    verify_manifest_entry_points,
)
from quant_platform.marketplace.manifest import PluginManifest, load_plugin_manifest, load_plugin_manifest_from_package
from quant_platform.marketplace.pip_runner import MarketplaceError, PipRunner
from quant_platform.marketplace.service import MarketplaceService

__all__ = [
    "MarketplaceError",
    "MarketplaceService",
    "PipRunner",
    "PluginManifest",
    "build_service",
    "discover_entry_points_from_manifest",
    "load_plugin_manifest",
    "load_plugin_manifest_from_package",
    "main",
    "register_plugins_from_manifest",
    "verify_manifest_entry_points",
]
