# Contributing to Pymplify

Install Python 3.10+, create a virtual environment, and run from the repository root:

```bash
python -m pip install -r requirements-dev.txt
python -m pip install -e ./packages/pymplify-core -e ./packages/pymplify-text -e ./packages/pymplify-tabular
python -m pytest --cov
```

Keep each change focused on one task or adapter. Before implementing a new area,
describe the user task, upstream project, its license, supported versions, and the
expected reduction in code. Do not add heavy dependencies to core or introduce
placeholder APIs for capabilities that have not been implemented.

To create a package: `python tools/new_package.py <area>`. The generator only
creates the structure; implementation, tests, documentation, and CI integration
are still required. Advertise discovery through the `pymplify.adapters` entry
point group only after implementing a factory that returns an `Adapter` with
working `Operation` objects. See [the catalog API](docs/catalog-api.md). Factories
must defer heavy backend imports and perform no processing during discovery.

When changing an adapter, verify observable behavior: equivalence to a direct
upstream call, result shape, model reuse, and input errors. Examples must run
without secrets or paid services. Tests must not download models or access the
network. If future integrations require these operations, place them in a separate,
explicit test suite.

Before submitting a change:

```bash
python -m ruff check .
python -m ruff format --check .
python -m pytest --cov --cov-report=term-missing
python -m build packages/pymplify-core --outdir dist
python -m build packages/pymplify-text --outdir dist
python -m build packages/pymplify-tabular --outdir dist
python -m twine check dist/*
```

In the change description, explain the problem, resulting behavior, checks
performed, and limitations. Document public API changes in the documentation and
CHANGELOG. Contributions included in the project are distributed under MIT terms.
