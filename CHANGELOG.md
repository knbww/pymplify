# Changelog

## Unreleased

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
