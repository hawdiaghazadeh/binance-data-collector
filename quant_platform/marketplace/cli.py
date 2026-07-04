"""Marketplace CLI — install / enable / disable / update / remove."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from quant_platform.core.manager import PluginManager
from quant_platform.marketplace.config_store import PluginConfigStore
from quant_platform.marketplace.pip_runner import MarketplaceError
from quant_platform.marketplace.service import MarketplaceService
from quant_platform.marketplace.state import InstalledPluginStore
from quant_platform.registries.groups import ALL_REGISTRY_GROUPS


def build_service(
    *,
    config_path: Path | None = None,
    state_path: Path | None = None,
) -> MarketplaceService:
    manager = PluginManager()
    for group in ALL_REGISTRY_GROUPS:
        manager.discover(group)
    return MarketplaceService(
        manager,
        state_store=InstalledPluginStore(state_path or Path(".quant_platform/installed_plugins.yaml")),
        config_store=PluginConfigStore(config_path) if config_path is not None else None,
    )


def _format_listing(service: MarketplaceService, group: str | None, installed_only: bool) -> str:
    lines: list[str] = []
    for item in service.list_plugins(group=group, installed_only=installed_only):
        status = item.status.value
        package = f" ({item.package})" if item.package else ""
        lines.append(f"{item.group}:{item.metadata.name} v{item.metadata.version} [{status}]{package}")
    return "\n".join(lines) if lines else "No plugins found."


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="quant-plugins", description="Quant platform plugin marketplace CLI")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/config.yaml"),
        help="Application config path for enable/disable persistence",
    )
    parser.add_argument(
        "--state",
        type=Path,
        default=Path(".quant_platform/installed_plugins.yaml"),
        help="Installed plugin state file",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List registered plugins")
    list_parser.add_argument("--group", help="Filter by registry group")
    list_parser.add_argument("--installed", action="store_true", help="Show marketplace-installed plugins only")

    install_parser = subparsers.add_parser("install", help="Install a plugin package via pip")
    install_parser.add_argument("package", help="Package spec for pip install")
    install_parser.add_argument("--group", help="Limit discovery to one registry group")

    enable_parser = subparsers.add_parser("enable", help="Enable a registered plugin")
    enable_parser.add_argument("group", help="Registry group")
    enable_parser.add_argument("name", help="Plugin name")

    disable_parser = subparsers.add_parser("disable", help="Disable a registered plugin")
    disable_parser.add_argument("group", help="Registry group")
    disable_parser.add_argument("name", help="Plugin name")

    update_parser = subparsers.add_parser("update", help="Upgrade an installed plugin package")
    update_parser.add_argument("group", help="Registry group")
    update_parser.add_argument("name", help="Plugin name")

    remove_parser = subparsers.add_parser("remove", help="Remove a plugin from the registry")
    remove_parser.add_argument("group", help="Registry group")
    remove_parser.add_argument("name", help="Plugin name")
    remove_parser.add_argument(
        "--keep-package",
        action="store_true",
        help="Unregister only; do not pip uninstall",
    )

    inspect_parser = subparsers.add_parser("inspect", help="Show plugin.yaml manifest for a package")
    inspect_parser.add_argument("package", help="Python package containing plugin.yaml")

    args = parser.parse_args(argv)
    service = build_service(config_path=args.config, state_path=args.state)

    try:
        if args.command == "list":
            print(_format_listing(service, args.group, args.installed))
            return 0

        if args.command == "install":
            result = service.install(args.package, group=args.group)
            for plugin in result.installed:
                print(f"installed {plugin.group}:{plugin.name} v{plugin.version} from {result.package}")
            return 0

        if args.command == "enable":
            service.enable(args.group, args.name, persist=True)
            print(f"enabled {args.group}:{args.name}")
            return 0

        if args.command == "disable":
            service.disable(args.group, args.name, persist=True)
            print(f"disabled {args.group}:{args.name}")
            return 0

        if args.command == "update":
            result = service.update(args.group, args.name)
            if result.changed:
                print(f"updated {result.group}:{result.name} {result.old_version} -> {result.new_version}")
            else:
                print(f"{result.group}:{result.name} already at {result.new_version}")
            return 0

        if args.command == "remove":
            service.remove(args.group, args.name, uninstall_package=not args.keep_package)
            print(f"removed {args.group}:{args.name}")
            return 0

        if args.command == "inspect":
            inspection = service.inspect_package(args.package)
            manifest = inspection.manifest
            print(f"name: {manifest.name}")
            print(f"version: {manifest.version}")
            print(f"group: {manifest.registry_group}")
            print(f"package: {manifest.package}")
            for registry_group, plugins in manifest.entry_points.items():
                for name, target in plugins.items():
                    print(f"entry_point: {registry_group}:{name} -> {target}")
            if inspection.entry_point_mismatches:
                print("entry_point_mismatches:")
                for item in inspection.entry_point_mismatches:
                    print(f"  - {item}")
            return 0
    except MarketplaceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    parser.error(f"Unknown command: {args.command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
