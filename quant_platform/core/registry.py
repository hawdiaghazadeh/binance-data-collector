"""Base registry implementation."""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any, Generic, TypeVar

from quant_platform.core.plugin import DisableReason, PluginMetadata, PluginRecord, PluginStatus

T = TypeVar("T")


class RegistryError(Exception):
    """Raised for registry operation failures."""


class PluginUnavailableError(RegistryError):
    """Raised when a plugin cannot be instantiated."""

    def __init__(self, name: str, reason: DisableReason | None = None, message: str = "") -> None:
        self.name = name
        self.disable_reason = reason
        super().__init__(message or f"Plugin '{name}' is unavailable")


class BaseRegistry(Generic[T]):
    """Thread-safe plugin registry."""

    _instances: dict[str, BaseRegistry[Any]] = {}
    _lock = threading.Lock()

    def __init__(self, group: str) -> None:
        self._group = group
        self._records: dict[str, PluginRecord] = {}
        self._registry_lock = threading.Lock()

    @classmethod
    def get_instance(cls, group: str) -> BaseRegistry[Any]:
        with cls._lock:
            if group not in cls._instances:
                cls._instances[group] = BaseRegistry(group)
            return cls._instances[group]

    @property
    def group(self) -> str:
        return self._group

    def register(
        self,
        metadata: PluginMetadata,
        factory: Callable[..., T],
        *,
        status: PluginStatus | None = None,
        disable_reason: DisableReason | None = None,
    ) -> None:
        meta = metadata.model_copy(update={"registry_group": self._group})
        with self._registry_lock:
            if meta.name in self._records:
                raise RegistryError(f"Plugin '{meta.name}' already registered in {self._group}")
            record_status = status or meta.status
            self._records[meta.name] = PluginRecord(
                metadata=meta,
                factory=factory,
                status=record_status,
                disable_reason=disable_reason,
            )

    def unregister(self, name: str) -> None:
        with self._registry_lock:
            self._records.pop(name, None)

    def get_record(self, name: str) -> PluginRecord:
        with self._registry_lock:
            if name not in self._records:
                raise RegistryError(f"Plugin '{name}' not found in {self._group}")
            return self._records[name]

    def get(self, name: str, *, config: dict[str, Any] | None = None) -> T:
        record = self.get_record(name)
        if record.status != PluginStatus.ENABLED:
            raise PluginUnavailableError(name, record.disable_reason)
        if record.factory is None:
            raise PluginUnavailableError(name, record.disable_reason, "No factory registered")
        if config:
            return record.factory(config=config)
        return record.factory()

    def list_plugins(self, *, enabled_only: bool = False) -> list[PluginMetadata]:
        with self._registry_lock:
            records = list(self._records.values())
        if enabled_only:
            records = [r for r in records if r.status == PluginStatus.ENABLED]
        return [r.metadata for r in records]

    def set_status(
        self,
        name: str,
        status: PluginStatus,
        *,
        disable_reason: DisableReason | None = None,
        last_error: str | None = None,
    ) -> None:
        with self._registry_lock:
            if name not in self._records:
                raise RegistryError(f"Plugin '{name}' not found")
            record = self._records[name]
            record.status = status
            record.disable_reason = disable_reason
            if last_error is not None:
                record.last_error = last_error

    def mark_loaded(self, name: str) -> None:
        from datetime import datetime, timezone

        with self._registry_lock:
            if name in self._records:
                self._records[name].loaded_at = datetime.now(timezone.utc)
