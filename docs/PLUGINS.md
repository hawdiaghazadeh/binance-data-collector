# Plugin Authoring Guide

## Quick Start

1. Create a plugin package under `platform/plugins/your_plugin/`
2. Define `PLUGIN_METADATA` and `factory()`
3. Register via entry point in `pyproject.toml` or `@register` decorator

## Example

```python
from quant_platform.core.plugin import PluginMetadata, PluginLifecycle
from quant_platform.version import PLATFORM_VERSION

PLUGIN_METADATA = PluginMetadata(
    name="my_feature",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    lifecycle=PluginLifecycle.TRANSIENT,
    registry_group="platform.features",
)

class MyFeature:
    def compute(self, ctx):
        ...

def factory(**kwargs):
    return MyFeature()
```

## Entry Point

```toml
[project.entry-points."platform.features"]
my_feature = "quant_platform.plugins.my_feature:factory"
```

## Data Flow

Use `PipelineContext.emit()` / `require()` — never call other plugins directly.

## Lifecycle

- `singleton` — DB connections, shared services
- `transient` — stateless transforms (default)
- `scoped` — per pipeline run state

See [PLATFORM_ARCHITECTURE.md](PLATFORM_ARCHITECTURE.md) for full specification.
