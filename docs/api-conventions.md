# API conventions

## Public interface

- Distribution: `pymplify-<area>`; import: `pymplify_<area>`.
- Public objects are exported from `__init__.py` and listed in `__all__`.
- The main function is named after an action; the current example is `vectorize`.
- Required input is positional; settings are keyword arguments.
- The default call works without a configuration file.
- The result preserves access to the original model and native backend data.
- Public functions have annotations and docstrings; packages include `py.typed`.

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
all exceptions indiscriminately: memory errors, interruptions, and unexpected
upstream failures must remain distinguishable.

## Behavior and reproducibility

Do not change global state, the environment, network resources, or the filesystem
without making it explicit. Document long operations and model downloads in
future packages. Expose `random_state` or seed controls for stochastic backends.
Avoid silently selecting a GPU, changing dtype, or converting to dense arrays.
In v0.1, TF-IDF uses scikit-learn defaults and runs locally.

Verify adapter results against direct upstream calls, model reuse, and invalid
input behavior. Record tested versions in release notes; a dependency range alone
does not prove compatibility with every future version.
