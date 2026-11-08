"""Small, framework-independent building blocks for Pymplify packages."""

from pymplify_core.adapters import Adapter, Operation
from pymplify_core.catalog import Catalog, DiscoveryIssue, discover_adapters
from pymplify_core.dependencies import require_dependency
from pymplify_core.errors import (
    AdapterLoadError,
    AdapterNotFoundError,
    BackendError,
    ConfigurationError,
    MissingDependencyError,
    OperationNotFoundError,
    PymplifyError,
)

__all__ = [
    "Adapter",
    "AdapterLoadError",
    "AdapterNotFoundError",
    "BackendError",
    "Catalog",
    "ConfigurationError",
    "DiscoveryIssue",
    "MissingDependencyError",
    "Operation",
    "OperationNotFoundError",
    "PymplifyError",
    "discover_adapters",
    "require_dependency",
]
