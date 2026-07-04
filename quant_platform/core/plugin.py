"""Plugin metadata, status, and lifecycle types."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator
from packaging.version import Version, InvalidVersion
from packaging.specifiers import SpecifierSet, InvalidSpecifier


class PluginStatus(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    DEPRECATED = "deprecated"


class PluginLifecycle(str, Enum):
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


class DisableReason(str, Enum):
    USER_CONFIG = "user_config"
    INCOMPATIBLE_VERSION = "incompatible_version"
    LOAD_CRASH = "load_crash"
    DEPENDENCY_UNMET = "dependency_unmet"
    COMPATIBILITY_REJECTED = "compatibility_rejected"


class PluginDependency(BaseModel):
    name: str
    version: str = "*"


class PluginMetadata(BaseModel):
    name: str
    version: str
    platform_version_compatibility: str
    author: str = ""
    description: str = ""
    license: str = ""
    tags: list[str] = Field(default_factory=list)
    dependencies: list[PluginDependency] = Field(default_factory=list)
    compatible_dataset_versions: str | None = None
    compatible_feature_versions: str | None = None
    supported_markets: list[str] = Field(default_factory=list)
    supported_timeframes: list[str] = Field(default_factory=list)
    config_schema: dict[str, Any] = Field(default_factory=dict)
    input_types: list[str] = Field(default_factory=list)
    output_types: list[str] = Field(default_factory=list)
    status: PluginStatus = PluginStatus.ENABLED
    lifecycle: PluginLifecycle = PluginLifecycle.TRANSIENT
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    registry_group: str = ""

    @field_validator("version")
    @classmethod
    def validate_semver(cls, v: str) -> str:
        try:
            Version(v)
        except InvalidVersion as exc:
            raise ValueError(f"Invalid SemVer: {v}") from exc
        return v

    @field_validator("platform_version_compatibility")
    @classmethod
    def validate_platform_compat(cls, v: str) -> str:
        try:
            SpecifierSet(v)
        except InvalidSpecifier as exc:
            raise ValueError(f"Invalid version specifier: {v}") from exc
        return v


class PluginRecord(BaseModel):
    metadata: PluginMetadata
    factory: Any = None
    status: PluginStatus = PluginStatus.ENABLED
    disable_reason: DisableReason | None = None
    last_error: str | None = None
    loaded_at: datetime | None = None

    model_config = {"arbitrary_types_allowed": True}
