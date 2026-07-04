"""Persist plugin enable/disable preferences to YAML config."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class PluginConfigStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    def _load_root(self) -> dict[str, Any]:
        if not self._path.exists():
            return {}
        payload = yaml.safe_load(self._path.read_text(encoding="utf-8"))
        return dict(payload) if isinstance(payload, dict) else {}

    def _save_root(self, payload: dict[str, Any]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    def _plugins_section(self, payload: dict[str, Any]) -> dict[str, Any]:
        plugins = payload.setdefault("plugins", {})
        if not isinstance(plugins, dict):
            plugins = {}
            payload["plugins"] = plugins
        return plugins

    def enable_plugin(self, name: str) -> None:
        payload = self._load_root()
        plugins = self._plugins_section(payload)
        disabled = list(plugins.get("disabled", []) or [])
        plugins["disabled"] = [item for item in disabled if item != name]
        enabled = plugins.get("enabled")
        if isinstance(enabled, list) and name not in enabled:
            enabled.append(name)
            plugins["enabled"] = enabled
        self._save_root(payload)

    def disable_plugin(self, name: str) -> None:
        payload = self._load_root()
        plugins = self._plugins_section(payload)
        disabled = list(plugins.get("disabled", []) or [])
        if name not in disabled:
            disabled.append(name)
        plugins["disabled"] = disabled
        enabled = plugins.get("enabled")
        if isinstance(enabled, list):
            plugins["enabled"] = [item for item in enabled if item != name]
        self._save_root(payload)
