# Pymplify

**Complex AI/ML tools → standardized automation → minimal Python code.**

Pymplify is an independent open-source ecosystem of Python packages that simplify
existing AI/ML libraries. Each package addresses a specific task, is installed and
versioned independently, and preserves access to the original tools.

Stage: **v0.2.x — Expansion**, with an experimental API. Installed adapter discovery,
an operation catalog, text vectorization, and numerical feature standardization
are implemented. Automatic analysis of arbitrary libraries, steering, and neural
embeddings are not implemented.

## Quick start

Python **3.10+**. Clone the repository and create a virtual environment:

```bash
git clone https://github.com/knbww/pymplify.git
cd pymplify
python -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e ./packages/pymplify-core -e ./packages/pymplify-text -e ./packages/pymplify-tabular
python examples/text_vectors.py
python examples/adapter_catalog.py
```

These instructions install from source. The packages in this repository have not
been published to PyPI, and the availability of their names has not been checked.

```python
from pymplify_text import vectorize

result = vectorize(["Python simplifies learning", "Learning uses data"])
print(result.matrix.shape)  # (2, 5)
```

One call fits a TF-IDF vectorizer and returns the native SciPy sparse matrix and
the fitted scikit-learn model. Processing is local, with no model downloads.
TF-IDF uses word statistics rather than neural semantic embeddings.

New texts reuse the same vocabulary without refitting:

```python
queries = result.transform(["Python uses data"])
assert queries.model is result.model
```

All original `TfidfVectorizer` parameters are available when fitting:

```python
result = vectorize(
    ["simple model", "small model"],
    ngram_range=(1, 2),
    max_features=5_000,
)
print(result.model.get_feature_names_out())
```

## Discover supported operations

```python
from pymplify_core import discover_adapters

catalog = discover_adapters(strict=True)
for adapter in catalog.for_library("sklearn"):
    print(adapter.name, [operation.name for operation in adapter.operations])
# tabular ['scale']
# text ['vectorize']

result = catalog.run("text", "vectorize", ["small model", "simple model"])
scaled = catalog.run("tabular", "scale", [[1.0, 10.0], [2.0, 20.0], [3.0, 30.0]])
assert catalog.for_library("unsupported-library") == ()
```

Discovery reads installed `pymplify.adapters` entry points and calls their factories.
Built-in factories describe operations without importing scikit-learn. No operation
runs until explicitly called. With default non-strict discovery, inspect
`catalog.discovery_issues` for plugins that could not be loaded.

Register your own callable without changing Pymplify:

```python
from pymplify_core import Adapter, Operation

catalog.register(
    Adapter(
        name="custom",
        library="my-tools",
        operations=(Operation("word_count", lambda text: len(text.split()), "Count words."),),
    )
)
assert catalog.run("custom", "word_count", "one import one action") == 4
```

See the [adapter contract and catalog API](docs/catalog-api.md) for packaging a
custom adapter so it can be discovered in other applications.

## Principles

- **One Import, One Action:** a useful result in one call.
- **Zero Configuration:** sensible defaults without configuration files.
- **Full Control:** explicit parameters and access to the original objects.
- **Compatibility:** native result types and verifiable dependencies.
- **Modularity:** separate distributions without installing the entire ecosystem.
- **Open Source:** MIT licensing, open conventions, and a contribution process.

## Packages

| Distribution | Python import | Purpose | Version |
| --- | --- | --- | --- |
| [`pymplify-core`](packages/pymplify-core/) | `pymplify_core` | Adapter contracts, discovery, catalogs, and shared errors; no ML frameworks | 0.2.0 |
| [`pymplify-text`](packages/pymplify-text/) | `pymplify_text` | TF-IDF text vectorization through scikit-learn | 0.2.0 |
| [`pymplify-tabular`](packages/pymplify-tabular/) | `pymplify_tabular` | Numerical feature standardization through scikit-learn | 0.1.0 |

The root `pyproject.toml` contains development settings. The repository root is not
an installable package; a shared `import pymplify` interface does not exist yet.

## Current capabilities

Pymplify discovers installed adapters, lists supported operations by library,
and executes declared workflows. Both built-in adapters use scikit-learn;
`sklearn` is an explicit alias. Unknown library names return no matches.

Discovery covers packages that advertise the Pymplify adapter contract. It does
not discover arbitrary library functions, analyze GitHub repositories, or generate
simplification suggestions. `require_dependency` only imports a known module.
The package generator creates a scaffold; its operations must still be implemented
and tested by a developer.

```text
packages/
  pymplify-core/       # independent pyproject.toml, src/, tests/, LICENSE
  pymplify-text/       # independent pyproject.toml, src/, tests/, LICENSE
  pymplify-tabular/    # independent pyproject.toml, src/, tests/, LICENSE
docs/                 # architecture, API, roadmap, and releases
examples/             # runnable examples
templates/package/    # independent package templates
tools/new_package.py  # package creation from templates
.github/workflows/    # checks, builds, and wheel/sdist verification
```

## Development

After completing the quick start:

```bash
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m ruff format --check .
python -m pytest --cov --cov-report=term-missing
python -m build packages/pymplify-core --outdir dist
python -m build packages/pymplify-text --outdir dist
python -m build packages/pymplify-tabular --outdir dist
python -m twine check dist/*
```

To start a new area:

```bash
python tools/new_package.py audio
```

The generator creates `packages/pymplify-audio` with metadata, a license, and a
typed module. You then implement the operation and adapter factory, enable its
entry point, add dependencies and tests, and include the package in CI. Running it again will not overwrite an existing package.

## Documentation

- [Architecture and package boundaries](docs/architecture.md)
- [API conventions and error handling](docs/api-conventions.md)
- [Adapter contract and catalog API](docs/catalog-api.md)
- [Text vectorization API](docs/text-api.md)
- [Tabular preprocessing API](docs/tabular-api.md)
- [Roadmap](docs/roadmap.md)
- [Versioning and releases](docs/releases.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)
