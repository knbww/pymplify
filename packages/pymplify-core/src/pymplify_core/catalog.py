"""Per-instance adapter catalogs and opt-in installed plugin discovery."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from importlib.metadata import entry_points
from typing import Any

from pymplify_core.adapters import Adapter, _library_name
from pymplify_core.errors import AdapterLoadError, AdapterNotFoundError, ConfigurationError

ENTRY_POINT_GROUP = "pymplify.adapters"


@dataclass(frozen=True)
class DiscoveryIssue:
    """A skipped plugin and the reason it could not be registered."""

    name: str
    value: str
    error: AdapterLoadError


class Catalog:
    """An explicit collection of adapters; no shared global registration state."""

    def __init__(self, adapters: Iterable[Adapter] = ()) -> None:
        self._adapters: dict[str, Adapter] = {}
        self._discovery_issues: list[DiscoveryIssue] = []
        for adapter in adapters:
            self.register(adapter)

    @property
    def adapters(self) -> tuple[Adapter, ...]:
        """Registered adapters ordered by name, without executing operations."""
        return tuple(self._adapters[name] for name in sorted(self._adapters))

    @property
    def discovery_issues(self) -> tuple[DiscoveryIssue, ...]:
        """Failures skipped during non-strict discovery; never silently discarded."""
        return tuple(self._discovery_issues)

    def register(self, adapter: Adapter) -> None:
        """Add an adapter. Existing registrations cannot be overwritten."""
        if not isinstance(adapter, Adapter):
            raise ConfigurationError("Register an Adapter instance.")
        if adapter.name in self._adapters:
            raise ConfigurationError(f"Adapter '{adapter.name}' is already registered.")
        self._adapters[adapter.name] = adapter

    def get(self, name: str) -> Adapter:
        """Get an adapter by its exact identifier, or explain what is available."""
        try:
            return self._adapters[name]
        except KeyError as exc:
            available = ", ".join(adapter.name for adapter in self.adapters) or "none"
            raise AdapterNotFoundError(
                f"Adapter '{name}' is not registered. Available: {available}. "
                "Install an adapter package or register one explicitly."
            ) from exc

    def for_library(self, name: str) -> tuple[Adapter, ...]:
        """Find adapters by distribution name or explicit alias; return () if unsupported."""
        normalized = _library_name(name)
        return tuple(
            adapter
            for adapter in self.adapters
            if normalized in {_library_name(item) for item in (adapter.library, *adapter.aliases)}
        )

    def run(self, adapter: str, operation: str, /, *args: Any, **kwargs: Any) -> Any:
        """Execute a registered operation, preserving native results and exceptions."""
        return self.get(adapter).run(operation, *args, **kwargs)


def discover_adapters(*, strict: bool = False) -> Catalog:
    """Load factories advertised by installed packages in ``pymplify.adapters``.

    Factories must take no arguments and return an Adapter with the entry point's
    name. Discovery imports plugin code; factories should only describe operations
    and defer backend imports until execution. No packages are installed or scanned
    online. A fresh catalog is returned on every call.

    With ``strict=False``, broken plugins are skipped and recorded in
    ``catalog.discovery_issues``. With ``strict=True``, the first failure raises
    AdapterLoadError with its original cause. Operation errors are not intercepted.
    """
    catalog = Catalog()
    candidates = sorted(
        entry_points(group=ENTRY_POINT_GROUP), key=lambda item: (item.name, item.value)
    )
    for candidate in candidates:
        try:
            factory = candidate.load()
            adapter = factory()
            if not isinstance(adapter, Adapter) or adapter.name != candidate.name:
                raise ConfigurationError(
                    f"Entry point '{candidate.name}' must return an Adapter with the same name."
                )
            catalog.register(adapter)
        except Exception as exc:
            # The plugin loading boundary is deliberate: preserve a broken plugin's
            # cause while allowing independent installed adapters to remain usable.
            error = AdapterLoadError(
                f"Could not load adapter '{candidate.name}' from '{candidate.value}': {exc}"
            )
            if strict:
                raise error from exc
            error.__cause__ = exc
            catalog._discovery_issues.append(DiscoveryIssue(candidate.name, candidate.value, error))
    return catalog
