"""Pipeline runtime — compiled graph and resolved plugin handles (Phase 2B / G2)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.execution_graph import CompiledExecutionGraph, ExecutionStep
from quant_platform.core.manager import PluginManager
from quant_platform.registries.pipeline import (
    DATA_PROVIDER_GROUP,
    PARSER_GROUP,
    STORAGE_BACKEND_GROUP,
)

if TYPE_CHECKING:
    from quant_platform.plugins.binance_kline_parser import BinanceKlineParser
    from quant_platform.plugins.binance_vision import BinanceVisionDataProvider
    from quant_platform.plugins.clickhouse import ClickHouseStorageBackend


@dataclass(frozen=True)
class PipelineRuntime:
    """Startup-resolved pipeline: cached plugin instances + compiled execution graph."""

    manager: PluginManager
    data_provider: BinanceVisionDataProvider
    storage_backend: ClickHouseStorageBackend
    parser: BinanceKlineParser
    execution_graph: CompiledExecutionGraph

    def shutdown(self) -> None:
        self.manager.shutdown()


def compile_pipeline_graph(
    data_provider: Any,
    storage_backend: Any,
    parser: Any,
) -> CompiledExecutionGraph:
    """Build a frozen execution plan with zero registry lookup at runtime."""

    def emit_provider(ctx: PipelineContext) -> None:
        ctx.emit(DataEnvelope(type_key="data_provider", payload=data_provider))

    def emit_storage(ctx: PipelineContext) -> None:
        ctx.emit(DataEnvelope(type_key="storage_backend", payload=storage_backend))

    def emit_parser(ctx: PipelineContext) -> None:
        ctx.emit(DataEnvelope(type_key="parser", payload=parser))

    return CompiledExecutionGraph.from_handlers(
        [
            ("binance_vision", emit_provider, DATA_PROVIDER_GROUP),
            ("clickhouse", emit_storage, STORAGE_BACKEND_GROUP),
            ("binance_kline_csv", emit_parser, PARSER_GROUP),
        ]
    )


def materialize_runtime(
    manager: PluginManager,
    *,
    data_provider_name: str = "binance_vision",
    storage_backend_name: str = "clickhouse",
    parser_name: str = "binance_kline_csv",
) -> PipelineRuntime:
    """Resolve pipeline plugins once at startup and compile the execution graph."""
    data_provider = manager.get(DATA_PROVIDER_GROUP, data_provider_name)
    storage_backend = manager.get(STORAGE_BACKEND_GROUP, storage_backend_name)
    parser = manager.get(PARSER_GROUP, parser_name)
    graph = compile_pipeline_graph(data_provider, storage_backend, parser)
    return PipelineRuntime(
        manager=manager,
        data_provider=data_provider,
        storage_backend=storage_backend,
        parser=parser,
        execution_graph=graph,
    )
