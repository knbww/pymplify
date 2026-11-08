# Changelog

## Unreleased — Expansion

### pymplify-core 0.2.0

- Add validated `Adapter` and `Operation` descriptors and per-instance `Catalog` objects.
- Discover factories from installed `pymplify.adapters` entry points.
- Query supported libraries and aliases, inspect operations, and execute native callables.
- Support manual registration, explicit unknown-name errors, and broken-plugin diagnostics.
- Preserve operation exceptions and prevent duplicate registrations from overwriting adapters.

### pymplify-text 0.2.0

- Advertise the existing TF-IDF workflow as the `text` adapter's `vectorize` operation.
- Preserve direct imports and defer backend loading during discovery.
- Require the 0.2 core contract and add GitHub project URLs to distribution metadata.

### pymplify-tabular 0.1.0

- Add `scale` over `StandardScaler` with original data and fitted model access.
- Reuse training statistics for new samples without refitting.
- Advertise the `tabular` adapter and preserve sparse input with explicit configuration.

### Development and documentation

- Test real installed discovery, custom registration, plugin failures, and native backend equivalence.
- Extend CI and distribution smoke checks to all three packages and the catalog example.
- Add adapter registration instructions to package templates and documentation.
- Record successful Foundation CI and add GitHub URLs to package metadata.

- Translate all documentation, package README templates, and contribution templates into English.
- Clarify the current limits of library integration and automatic discovery in the README.

## Foundation 0.1.0 — 2026-11-08

Prepared the local foundation; not published to PyPI.

### pymplify-core 0.1.0

- Shared error hierarchy and on-demand dependency loading.
- Original exceptions preserved, with installation guidance for missing backends.

### pymplify-text 0.1.0

- `vectorize` wraps `TfidfVectorizer` with its native sparse matrix and model.
- `TextVectors.transform` processes new texts without refitting.
- Corpus validation and direct access to upstream parameters.

### Infrastructure

- Independent packages using the `src` layout and MIT licensing.
- Pytest, coverage, Ruff, CI, and wheel/sdist verification.
- Documentation, a runnable example, and a new-package generator.
