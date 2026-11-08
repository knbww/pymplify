# Roadmap

Versions represent ecosystem stages rather than a required list of libraries.
Packages are released independently and may have different version numbers.

| Stage | Focus | Completion criteria |
| --- | --- | --- |
| v0.1.x — Foundation | Structure, conventions, infrastructure, first adapter | Independent builds, a working example, tests, documentation, and verified CI |
| v0.2.x — Expansion | Supported library catalog, extensible adapters, a second task area | Discover installed adapters, list and run operations, register a custom adapter, verify compatibility |
| v0.3.x — Automation | Library/code analysis and simplification proposals | Explainable suggestions, explicit configuration, and behavioral validation of generated candidates |
| v0.4.x — Integration | Cooperation between packages | Shared workflows that preserve package independence |
| v1.0.0 — Stable | Stability and broad adoption | Defined APIs, a compatibility policy, and complete documentation |

## Foundation verification

The initial foundation was published at commit `31547d7`. Its
[CI run passed all eight jobs](https://github.com/knbww/pymplify/actions/runs/42499438645),
including Linux with Python 3.10/3.12/3.14, Windows and macOS with Python 3.12,
scikit-learn 1.4.2 compatibility, style checks, and distribution installation.
PyPI publication is separate and has not occurred.

## Current expansion

- Validated `Adapter` and `Operation` contracts in core.
- Per-instance catalogs and discovery through installed Python entry points.
- Library-name queries with explicit aliases and clear unsupported-library behavior.
- Operation dispatch preserving native results and exceptions.
- Manual registration of application-specific adapters without changes to core.
- Independent TF-IDF text and numerical scaling adapters, both using scikit-learn.
- Discovery diagnostics, collision handling, tests, examples, and package templates.

Core and text use version 0.2.0; the new tabular distribution starts at 0.1.0.
These are source versions; a version bump is not a PyPI publication or a GitHub
release tag. The updated CI must pass before treating the expansion as verified.

## Next decisions

The source repository is [knbww/pymplify](https://github.com/knbww/pymplify).
Before a PyPI release, check distribution names, record compatibility evidence,
and verify the chosen release artifacts in a clean environment.

Automatic analysis is a separate stage. Start with describing available functions
and identifying repeated workflows in user-provided code. Proposals should include
what changes and how to validate equivalence. Do not equate function discovery
with reliable automatic understanding of every library.

Steering, image processing, neural embeddings, and inference remain possible
adapter directions without promised timelines. Each needs a real user task,
selected upstream library, resource requirements, and outcome validation.
