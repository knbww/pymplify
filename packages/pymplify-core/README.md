# pymplify-core

The shared layer of the **Pymplify** ecosystem. Python 3.10+, MIT. No ML framework
dependencies. Provides explicit adapter contracts, a per-instance operation
catalog, installed plugin discovery, shared errors, and dependency loading.

From the repository root:

```bash
python -m pip install -e ./packages/pymplify-core
```

Core alone works without adapters and does not install any. Discover available
adapters after installing their distributions:

```python
from pymplify_core import discover_adapters

catalog = discover_adapters(strict=True)
print([adapter.name for adapter in catalog.adapters])
print(catalog.for_library("sklearn"))
```

Register an application-specific callable without an installed plugin:

```python
from pymplify_core import Adapter, Catalog, Operation

catalog = Catalog([Adapter("custom", "my-tools", (Operation("double", lambda value: value * 2),))])
assert catalog.run("custom", "double", 21) == 42
```

`Adapter` and `Operation` describe supported workflows; the catalog preserves
native results and exceptions. `discover_adapters()` reads installed entry points
in group `pymplify.adapters` and calls no-argument factories. It imports plugin
code but does not execute declared operations. Built-in factories keep ML
libraries unloaded until execution. No global registry or automatic installation
is used.

Default non-strict discovery skips broken plugins and records them in
`catalog.discovery_issues`. Strict discovery raises `AdapterLoadError`, with the
original cause preserved. Duplicate names cannot overwrite existing registrations.
Unknown libraries return no matches; unknown adapter and operation identifiers
raise `AdapterNotFoundError` and `OperationNotFoundError`.

## Shared errors

| Object | Purpose |
| --- | --- |
| `PymplifyError` | Base error for the ecosystem |
| `ConfigurationError` | Invalid input, configuration, or adapter contract; also a `ValueError` |
| `MissingDependencyError` | Missing backend; also an `ImportError` |
| `BackendError` | Backend operation failure; also a `RuntimeError` |
| `AdapterLoadError` | Failed plugin import, factory, or registration; also an `ImportError` |
| `AdapterNotFoundError` | Unknown adapter; also a `LookupError` |
| `OperationNotFoundError` | Unknown adapter operation; also a `LookupError` |

## Lazy dependency loading

```python
from pymplify_core import MissingDependencyError, require_dependency

try:
    backend = require_dependency(
        "sklearn.feature_extraction.text", install="scikit-learn>=1.4.2,<2"
    )
except MissingDependencyError as error:
    print(error)  # Installation guidance; nothing is installed automatically.
```

The original exception is preserved in `__cause__`. Missing internal backend
dependencies and incompatible binary extensions propagate without being masked.
`install` is guidance text, not an executed command.

After installation, get the distribution version with
`importlib.metadata.version("pymplify-core")`.

Reference: [adapter contract and catalog API](https://github.com/knbww/pymplify/blob/main/docs/catalog-api.md).
