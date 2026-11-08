# Adapter contract and operation catalog

The catalog connects applications to explicitly supported workflows. It does not
infer arbitrary APIs or install libraries automatically. Direct package imports
remain available; the catalog is optional.

## Discover installed adapters

Install core and the adapters you need. From this repository:

```bash
python -m pip install -e ./packages/pymplify-core -e ./packages/pymplify-text -e ./packages/pymplify-tabular
```

```python
from pymplify_core import discover_adapters

catalog = discover_adapters(strict=True)
print([adapter.name for adapter in catalog.adapters])  # ['tabular', 'text']
for adapter in catalog.for_library("scikit-learn"):
    print(adapter.name, [operation.name for operation in adapter.operations])

result = catalog.run("text", "vectorize", ["small model", "simple model"])
scaled = catalog.run("tabular", "scale", [[1.0, 10.0], [2.0, 20.0], [3.0, 30.0]])
```

Discovery reads the `pymplify.adapters` group of installed Python entry points.
Source code on `PYTHONPATH` alone is insufficient: install the distribution to
create its entry point metadata. A fresh catalog is created on each discovery
call; there is no global registry or implicit refresh after installation.

Discovery imports advertised plugin code and calls no-argument factories. Built-in
factories only construct descriptors and keep NumPy, SciPy, and scikit-learn
unloaded. Third-party factories are responsible for following the same convention.
Discovery does not invoke operations, download models, or scan online repositories.

## Public objects

| Object | Behavior |
| --- | --- |
| `Operation(name, function, description="")` | An immutable descriptor of a callable; calling it forwards arguments, return values, and exceptions |
| `Adapter(name, library, operations, description="", aliases=())` | An immutable adapter descriptor with at least one uniquely named operation |
| `Catalog(adapters=())` | An independent mutable collection of adapter registrations |
| `catalog.adapters` | A tuple of registered descriptors sorted by adapter name |
| `catalog.register(adapter)` | Register an adapter; duplicate names are rejected without replacement |
| `catalog.get(name)` | Look up an exact adapter identifier |
| `catalog.for_library(name)` | Find adapters by normalized distribution name or declared alias; return `()` if unsupported |
| `catalog.run(adapter, operation, /, *args, **kwargs)` | Execute one operation without changing its result or exceptions |
| `adapter.operation(name)` | Inspect an operation without running it |
| `adapter.run(operation, /, *args, **kwargs)` | Execute an operation directly through a descriptor |
| `discover_adapters(strict=False)` | Discover advertised factories and return a catalog |
| `catalog.discovery_issues` | A tuple of skipped plugins described by `DiscoveryIssue(name, value, error)` |

Adapter and operation identifiers must start with a lowercase ASCII letter and
contain only lowercase letters, digits, underscores, or hyphens. Identifiers are
case-sensitive. Library queries trim whitespace, ignore case, and treat runs of
hyphens, underscores, and dots as equivalent. Import names such as `sklearn` must
be declared as aliases; they are not guessed.

Descriptors snapshot operation and alias collections into tuples. Callables,
their state, and operation results remain under the original library's control.
Two adapters may support the same library; callers select an adapter explicitly
to avoid ambiguous operation routing. Dispatch identifiers are positional-only,
so upstream keyword arguments named `adapter`, `operation`, or `self` pass through.

## Register your own callable

```python
from pymplify_core import Adapter, Catalog, Operation


def word_count(text):
    return len(text.split())


catalog = Catalog()
catalog.register(
    Adapter(
        name="custom",
        library="my-tools",
        operations=(Operation("word_count", word_count, "Count whitespace-separated words."),),
    )
)
assert catalog.run("custom", "word_count", "one import one action") == 4
```

Explicit registration requires no entry point or package installation and affects
only that catalog. `Catalog` does not import, inspect, or execute the callable
during registration. This makes it suitable for application-specific workflows.

## Package an adapter for discovery

Provide a lightweight factory, for example in `my_package/adapter.py`:

```python
from pymplify_core import Adapter, Operation
from my_package.operations import predict


def get_adapter():
    return Adapter(
        name="my-model",
        library="my-upstream-library",
        operations=(Operation("predict", predict, "Run the supported prediction workflow."),),
    )
```

The example names represent your own implementation. `predict` must already be
implemented; importing its module must not load heavy backends or run a workflow.
Add the core dependency and entry point to your distribution's `pyproject.toml`:

```toml
[project]
dependencies = ["pymplify-core>=0.2.0,<0.3"]

[project.entry-points."pymplify.adapters"]
my-model = "my_package.adapter:get_adapter"
```

The entry point name must match `Adapter.name`. The loaded object must be a
no-argument factory returning an `Adapter` from the installed core API.
The factory can be called more than once; it must not depend on global registration
or perform training, downloads, or other processing. Install the distribution,
then call `discover_adapters()` again. No changes to core are needed.

The package generator includes a commented entry point example. Enable it only
after implementing the factory and operations; empty scaffolds do not advertise
unsupported functionality.

## Failures and conflicts

In default discovery mode, a broken import, factory exception, invalid descriptor,
or duplicate adapter name is skipped and recorded. Inspect these issues explicitly:

```python
catalog = discover_adapters()
for issue in catalog.discovery_issues:
    print(issue.name, issue.value, issue.error, issue.error.__cause__)
```

With `strict=True`, the first problem raises `AdapterLoadError`, preserving the
original exception in `__cause__`. Entries are processed in `(name, value)` order.
On conflicts, the first successfully registered entry remains; later registrations
are reported rather than overwriting it. Resolve the installed package conflict
or use explicit registration when a particular implementation is required.

Unknown adapter identifiers raise `AdapterNotFoundError`; unknown operations raise
`OperationNotFoundError`. Both inherit `PymplifyError` and `LookupError` and list
available choices. Invalid contracts and duplicate manual registrations raise
`ConfigurationError`.

The plugin-loading boundary records ordinary exceptions so one broken plugin does
not prevent other adapters from being discovered. Interruptions are not caught.
Once an operation is called, its errors propagate unchanged through the catalog;
individual adapters retain their documented error policy.

References: [Python entry point discovery](https://docs.python.org/3.10/library/importlib.metadata.html#entry-points),
[entry points specification](https://packaging.python.org/en/latest/specifications/entry-points/).
