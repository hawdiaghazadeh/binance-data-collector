"""Dependency graph resolution (Phase 2B)."""

from __future__ import annotations

from dataclasses import dataclass, field

from quant_platform.core.plugin import DisableReason, PluginStatus
from quant_platform.core.registry import BaseRegistry, RegistryError


@dataclass
class DependencyNode:
    name: str
    dependencies: list[str] = field(default_factory=list)
    status: PluginStatus = PluginStatus.ENABLED
    disable_reason: DisableReason | None = None


class DependencyResolver:
    """Build and resolve plugin dependency DAG."""

    def __init__(self) -> None:
        self._nodes: dict[str, DependencyNode] = {}

    def add_node(
        self,
        name: str,
        dependencies: list[str],
        *,
        status: PluginStatus = PluginStatus.ENABLED,
        disable_reason: DisableReason | None = None,
    ) -> None:
        self._nodes[name] = DependencyNode(
            name=name,
            dependencies=dependencies,
            status=status,
            disable_reason=disable_reason,
        )

    def topological_sort(self) -> list[str]:
        """Return load order; raise on cycle."""
        visited: set[str] = set()
        temp: set[str] = set()
        order: list[str] = []

        def visit(name: str) -> None:
            if name in temp:
                raise RegistryError(f"Circular dependency detected involving '{name}'")
            if name in visited:
                return
            temp.add(name)
            node = self._nodes.get(name)
            if node:
                for dep in node.dependencies:
                    if dep in self._nodes:
                        visit(dep)
            temp.remove(name)
            visited.add(name)
            order.append(name)

        for name in self._nodes:
            if name not in visited:
                visit(name)
        return order

    def cascade_disabled(self) -> dict[str, DisableReason]:
        """Mark dependents of disabled/failed plugins as dependency_unmet."""
        changed: dict[str, DisableReason] = {}
        for _ in range(len(self._nodes)):
            for name, node in self._nodes.items():
                if node.status != PluginStatus.ENABLED:
                    continue
                for dep in node.dependencies:
                    dep_node = self._nodes.get(dep)
                    if dep_node and dep_node.status != PluginStatus.ENABLED:
                        node.status = PluginStatus.DISABLED
                        node.disable_reason = DisableReason.DEPENDENCY_UNMET
                        changed[name] = DisableReason.DEPENDENCY_UNMET
        return changed

    def get_node(self, name: str) -> DependencyNode | None:
        return self._nodes.get(name)

    @classmethod
    def from_registry(cls, registry: BaseRegistry) -> DependencyResolver:
        resolver = cls()
        for meta in registry.list_plugins():
            record = registry.get_record(meta.name)
            deps = [d.name for d in meta.dependencies]
            resolver.add_node(
                meta.name,
                deps,
                status=record.status,
                disable_reason=record.disable_reason,
            )
        return resolver
