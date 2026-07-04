"""Pip subprocess helpers for marketplace install/update/remove."""

from __future__ import annotations

import subprocess
import sys
from typing import Protocol


class MarketplaceError(Exception):
    """Raised when a marketplace operation fails."""


class PipRunnerProtocol(Protocol):
    def install(self, package: str) -> None: ...

    def upgrade(self, package: str) -> None: ...

    def uninstall(self, package: str) -> None: ...


class PipRunner:
    def _run(self, args: list[str]) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "pip", *args],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            message = (result.stderr or result.stdout or "pip command failed").strip()
            raise MarketplaceError(message)

    def install(self, package: str) -> None:
        self._run(["install", package])

    def upgrade(self, package: str) -> None:
        self._run(["install", "--upgrade", package])

    def uninstall(self, package: str) -> None:
        self._run(["uninstall", "-y", package])
