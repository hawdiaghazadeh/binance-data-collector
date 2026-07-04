"""Installed plugin state persistence (Phase 22)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class InstalledPlugin:
    group: str
    name: str
    package: str
    version: str
    installed_at: str


class InstalledPluginStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> list[InstalledPlugin]:
        if not self._path.exists():
            return []
        payload = yaml.safe_load(self._path.read_text(encoding="utf-8")) or {}
        entries = payload.get("plugins", [])
        return [
            InstalledPlugin(
                group=item["group"],
                name=item["name"],
                package=item["package"],
                version=item["version"],
                installed_at=item.get("installed_at", ""),
            )
            for item in entries
            if isinstance(item, dict) and {"group", "name", "package", "version"} <= set(item)
        ]

    def save(self, plugins: list[InstalledPlugin]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "plugins": [
                {
                    "group": plugin.group,
                    "name": plugin.name,
                    "package": plugin.package,
                    "version": plugin.version,
                    "installed_at": plugin.installed_at,
                }
                for plugin in plugins
            ]
        }
        self._path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    def add(self, plugin: InstalledPlugin) -> None:
        plugins = [item for item in self.load() if not (item.group == plugin.group and item.name == plugin.name)]
        plugins.append(plugin)
        self.save(plugins)

    def remove(self, group: str, name: str) -> InstalledPlugin | None:
        plugins = self.load()
        removed: InstalledPlugin | None = None
        kept: list[InstalledPlugin] = []
        for item in plugins:
            if item.group == group and item.name == name:
                removed = item
            else:
                kept.append(item)
        self.save(kept)
        return removed

    def get_package(self, group: str, name: str) -> str | None:
        for item in self.load():
            if item.group == group and item.name == name:
                return item.package
        return None

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()
