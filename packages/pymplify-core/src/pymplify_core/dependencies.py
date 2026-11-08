"""Load backends on demand without installing or modifying anything."""

from importlib import import_module
from types import ModuleType

from pymplify_core.errors import MissingDependencyError


def require_dependency(module: str, *, install: str) -> ModuleType:
    """Import a backend or raise an actionable error when it is missing.

    ``install`` is a distribution or extra, e.g. ``scikit-learn>=1.4.2,<2``.
    Missing transitive dependencies and other import failures propagate intact:
    a broken installation must not be mistaken for an absent backend.
    """
    try:
        return import_module(module)
    except ModuleNotFoundError as exc:
        if exc.name is None or not (module == exc.name or module.startswith(exc.name + ".")):
            raise
        raise MissingDependencyError(
            f"Backend '{module}' is unavailable. Install it with: "
            f'python -m pip install "{install}"'
        ) from exc
