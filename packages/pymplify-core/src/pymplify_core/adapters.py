"""Explicit adapter contracts, with no imports of upstream ML libraries."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pymplify_core.errors import ConfigurationError, OperationNotFoundError


def _identifier(value: str, *, field: str) -> None:
    if not isinstance(value, str) or re.fullmatch(r"[a-z][a-z0-9_-]*", value) is None:
        raise ConfigurationError(f"{field} must be a lowercase identifier, e.g. 'text'.")


def _library_name(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError("Library names and aliases must be non-empty strings.")
    return re.sub(r"[-_.]+", "-", value.strip()).casefold()


@dataclass(frozen=True)
class Operation:
    """A named callable and its user-facing description. Execution is explicit."""

    name: str
    function: Callable[..., Any]
    description: str = ""

    def __post_init__(self) -> None:
        _identifier(self.name, field="Operation name")
        if not callable(self.function):
            raise ConfigurationError("Operation function must be callable.")
        if not isinstance(self.description, str):
            raise ConfigurationError("Operation description must be a string.")

    def __call__(self, /, *args: Any, **kwargs: Any) -> Any:
        """Return the original result and preserve the callable's exceptions."""
        return self.function(*args, **kwargs)


@dataclass(frozen=True)
class Adapter:
    """Operations for one upstream library, registered under a unique name.

    ``library`` is the distribution name; ``aliases`` may include import names,
    such as ``sklearn`` for ``scikit-learn``. No backend is loaded by this object.
    """

    name: str
    library: str
    operations: tuple[Operation, ...]
    description: str = ""
    aliases: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _identifier(self.name, field="Adapter name")
        _library_name(self.library)
        if not isinstance(self.description, str):
            raise ConfigurationError("Adapter description must be a string.")
        if isinstance(self.aliases, str):
            raise ConfigurationError("aliases must be a sequence of library names.")
        try:
            operations = tuple(self.operations)
            aliases = tuple(self.aliases)
        except TypeError as exc:
            raise ConfigurationError("operations and aliases must be iterable.") from exc
        if not operations or not all(isinstance(item, Operation) for item in operations):
            raise ConfigurationError("An adapter must provide at least one Operation.")
        if len({item.name for item in operations}) != len(operations):
            raise ConfigurationError("Operation names must be unique within an adapter.")
        for alias in aliases:
            _library_name(alias)
        object.__setattr__(self, "operations", operations)
        object.__setattr__(self, "aliases", aliases)

    def operation(self, name: str) -> Operation:
        """Look up an operation without running it."""
        for operation in self.operations:
            if operation.name == name:
                return operation
        available = ", ".join(item.name for item in self.operations)
        raise OperationNotFoundError(
            f"Adapter '{self.name}' has no operation '{name}'. Available: {available}."
        )

    def run(self, operation: str, /, *args: Any, **kwargs: Any) -> Any:
        """Execute one declared operation without changing its result or errors."""
        return self.operation(operation)(*args, **kwargs)
