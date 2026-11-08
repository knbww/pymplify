# pymplify-core

The shared layer of the **Pymplify** ecosystem. Python 3.10+, MIT. No ML framework
dependencies.

Run from the repository root:

```bash
python -m pip install -e ./packages/pymplify-core
```

```python
from pymplify_core import MissingDependencyError, require_dependency

try:
    backend = require_dependency(
        "sklearn.feature_extraction.text", install="scikit-learn>=1.4.2,<2"
    )
except MissingDependencyError as error:
    print(error)  # Installation guidance; nothing is installed automatically.
```

Public objects:

| Object | Purpose |
| --- | --- |
| `PymplifyError` | Base error for the ecosystem |
| `ConfigurationError` | Invalid input or configuration; also a `ValueError` |
| `MissingDependencyError` | Missing backend; also an `ImportError` |
| `BackendError` | Backend operation failure; also a `RuntimeError` |
| `require_dependency(module, *, install)` | Lazy import with installation guidance |

The original exception is preserved in `__cause__`. Missing internal backend
dependencies and incompatible binary extensions propagate without being masked.
`install` is guidance text, not an executed command.

After installation, get the distribution version with
`importlib.metadata.version("pymplify-core")`.
