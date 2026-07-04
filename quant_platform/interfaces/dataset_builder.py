"""Dataset builder protocol."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class DatasetBuilderProtocol(Protocol):
    def build(self, config: dict[str, Any] | None = None) -> Any: ...
