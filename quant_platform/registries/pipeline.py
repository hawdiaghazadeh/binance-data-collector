"""Registry singletons for pipeline plugins."""

from __future__ import annotations

from quant_platform.core.registry import BaseRegistry
from quant_platform.interfaces.data_provider import DataProviderProtocol
from quant_platform.interfaces.dataset_builder import DatasetBuilderProtocol
from quant_platform.interfaces.parser import ParserProtocol
from quant_platform.interfaces.storage_backend import StorageBackendProtocol

DATA_PROVIDER_GROUP = "platform.data_providers"
STORAGE_BACKEND_GROUP = "platform.storage_backends"
PARSER_GROUP = "platform.parsers"
DATASET_BUILDER_GROUP = "platform.dataset_builders"

data_provider_registry: BaseRegistry[DataProviderProtocol] = BaseRegistry.get_instance(
    DATA_PROVIDER_GROUP
)
storage_backend_registry: BaseRegistry[StorageBackendProtocol] = BaseRegistry.get_instance(
    STORAGE_BACKEND_GROUP
)
parser_registry: BaseRegistry[ParserProtocol] = BaseRegistry.get_instance(PARSER_GROUP)
dataset_builder_registry: BaseRegistry[DatasetBuilderProtocol] = BaseRegistry.get_instance(
    DATASET_BUILDER_GROUP
)
