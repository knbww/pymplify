# API conventions

## Public interface

- Distribution: `pymplify-<area>`; import: `pymplify_<area>`.
- Public objects are exported from `__init__.py` and listed in `__all__`.
- The main function is named after an action; the current example is `vectorize`.
- Required input is positional; settings are keyword arguments.
- The default call works without a configuration file.
- The result preserves access to the original model and native backend data.
- Public functions have annotations and docstrings; packages include `py.typed`.
- Discoverable packages expose a no-argument factory returning an `Adapter` with
  named `Operation` objects through the `pymplify.adapters` entry point group.
- Factories only describe operations; backend loading and processing happen at execution.
- Direct package APIs remain usable without creating or discovering a catalog.

Do not promise to support every upstream feature through one shortened call.
Document the supported workflow and preserve original objects for other tasks.

## Errors

```python
from pymplify_core import BackendError, ConfigurationError, PymplifyError
from pymplify_text import vectorize

try:
    result = vectorize(["example document"])
except ConfigurationError as error:
    print("Correct the input or options:", error)
except BackendError as error:
    print("Operation failed:", error)
    print("Original cause:", error.__cause__)
except PymplifyError as error:
    print(error)
```

`ConfigurationError` covers Pymplify's validation and constructor errors.
`TypeError` and `ValueError` raised during TF-IDF operations are wrapped in
`BackendError`. Scikit-learn validates some parameters only during `fit_transform`;
these failures also become `BackendError`, with the original message and cause
preserved.

A missing backend raises `MissingDependencyError` with an installation command.
Errors within a broken backend installation propagate unchanged. Do not catch
all execution exceptions indiscriminately: memory errors, interruptions, and
unexpected upstream failures must remain distinguishable. The explicit plugin
loading boundary records ordinary factory/import failures to isolate broken
plugins; strict mode raises `AdapterLoadError` with the original cause. Operation
exceptions pass through the catalog unchanged.

## Behavior and reproducibility

Do not change global state, the environment, network resources, or the filesystem
without making it explicit. Document long operations and model downloads in
future packages. Expose `random_state` or seed controls for stochastic backends.
Avoid silently selecting a GPU, changing dtype, or converting to dense arrays.
TF-IDF and numerical standardization use scikit-learn defaults and run locally.

Verify adapter results against direct upstream calls, model reuse, and invalid
input behavior. Record tested versions in release notes; a dependency range alone
does not prove compatibility with every future version.

See [adapter contracts and catalog behavior](catalog-api.md) for naming, discovery, and registration.

## Analysis and validation

Static inspection must never import or execute target source. Suggestions carry
source evidence, assumptions, and validation steps and remain marked unverified.
Do not label a name-pattern match as semantically equivalent or automatically
apply an edit. Execution-based validation requires explicit callables, cases, and
a domain comparator; its result covers those cases only. See the
[analysis API](analysis-api.md) for limits and failure behavior.
