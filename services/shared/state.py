"""Persistent state tracking for resumable downloads and imports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class StateStore:
    """
    JSON-based state store for tracking completed downloads and imports.

    Enables resume after restart without re-processing finished work.
    """

    def __init__(self, state_dir: Path, name: str) -> None:
        self._path = state_dir / f"{name}.json"
        self._data: dict[str, Any] = {"completed": [], "failed": []}
        self._load()

    def _load(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if self._path.exists():
            with self._path.open(encoding="utf-8") as fh:
                self._data = json.load(fh)

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as fh:
            json.dump(self._data, fh, indent=2)

    def is_completed(self, key: str) -> bool:
        return key in self._data.get("completed", [])

    def is_failed(self, key: str) -> bool:
        return key in self._data.get("failed", [])

    def mark_completed(self, key: str) -> None:
        completed: list[str] = self._data.setdefault("completed", [])
        if key not in completed:
            completed.append(key)
        failed: list[str] = self._data.get("failed", [])
        if key in failed:
            failed.remove(key)
        self._save()

    def mark_failed(self, key: str) -> None:
        failed: list[str] = self._data.setdefault("failed", [])
        if key not in failed:
            failed.append(key)
        self._save()

    def clear_failed(self, key: str) -> None:
        failed: list[str] = self._data.get("failed", [])
        if key in failed:
            failed.remove(key)
            self._save()

    @property
    def completed_count(self) -> int:
        return len(self._data.get("completed", []))
