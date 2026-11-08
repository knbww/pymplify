# Versioning and releases

Each distribution has its own version in its `pyproject.toml`.
Package versions do not have to match. The ecosystem stage in the roadmap does
not automatically determine the version of every package.

Before 1.0, a breaking change requires a minor version increment and migration
notes; patch releases are for compatible fixes. After 1.0, use SemVer.
Changes to public exports, result behavior, and exceptions count as API changes.

## Preparation

1. Check PyPI name availability and publishing permissions. Names in this
   repository have not been reserved; registry installation is not yet documented
   as a working option.
2. Update the selected package's version and changelog; record tested Python and
   upstream versions. Change the dependency on core only when necessary.
3. Run lint, formatting checks, tests, and CI on supported platforms.
4. Build the package being released and check its README and license:

```bash
python -m build packages/pymplify-core --outdir dist/pymplify-core
python -m twine check dist/pymplify-core/*
```

For text or tabular, change the path. Publish core before an adapter requiring its
new contract version. Core and text are currently 0.2.0; tabular starts at 0.1.0.

## Artifact verification

Install the wheel in a clean environment and run the example. To check all three
packages locally before their first publication:

```bash
python -m build packages/pymplify-core --outdir dist/expansion
python -m build packages/pymplify-text --outdir dist/expansion
python -m build packages/pymplify-tabular --outdir dist/expansion
python -m venv .venv-release
# Linux/macOS; Windows: .venv-release\Scripts\python.exe
# POSIX shell; PowerShell can pass each wheel path explicitly.
.venv-release/bin/python -m pip install dist/expansion/*.whl
.venv-release/bin/python examples/text_vectors.py
.venv-release/bin/python examples/tabular_scaling.py
.venv-release/bin/python examples/adapter_catalog.py
```

Use a fresh output directory so older wheels cannot conflict with the versions
being verified. CI explicitly installs all three wheels from local paths and runs
the direct examples and catalog discovery example.
The default build also verifies that a wheel can be built from the sdist.

## Publishing

Publishing is a separate action by the project owner after artifact verification,
first to TestPyPI and then to PyPI. This foundation does not include automatic
publishing or configured external accounts. Secrets must not be stored in the
repository. The recommended tag format for a distribution is `pymplify-text-v0.2.0`.
