"""Plugin instance lifecycle management (Phase 2B)."""

from __future__ import annotations

import threading
from typing import Any

from quant_platform.core.plugin import PluginLifecycle


class InstanceManager:
    """Manage singleton, transient, and scoped plugin instances."""

    def __init__(self) -> None:
        self._singletons: dict[str, Any] = {}
        self._scoped: dict[str, dict[str, Any]] = {}
        self._singleton_lock = threading.Lock()
        self._scoped_lock = threading.Lock()

    def get_or_create(
        self,
        key: str,
        lifecycle: PluginLifecycle,
        factory: Any,
        *,
        run_id: str | None = None,
        config: dict | None = None,
    ) -> Any:
        if lifecycle == PluginLifecycle.TRANSIENT:
            return factory(config=config) if config else factory()

        if lifecycle == PluginLifecycle.SINGLETON:
            if key not in self._singletons:
                with self._singleton_lock:
                    if key not in self._singletons:
                        self._singletons[key] = factory(config=config) if config else factory()
            return self._singletons[key]

        if lifecycle == PluginLifecycle.SCOPED:
            rid = run_id or "default"
            with self._scoped_lock:
                if rid not in self._scoped:
                    self._scoped[rid] = {}
                if key not in self._scoped[rid]:
                    self._scoped[rid][key] = factory(config=config) if config else factory()
                return self._scoped[rid][key]

        return factory(config=config) if config else factory()

    def clear_scoped(self, run_id: str) -> None:
        with self._scoped_lock:
            self._scoped.pop(run_id, None)

    def shutdown(self) -> None:
        with self._singleton_lock:
            self._singletons.clear()
        with self._scoped_lock:
            self._scoped.clear()
