# Roadmap

Versions represent ecosystem stages rather than a required list of libraries.
Packages are released independently and may have different version numbers.

| Stage | Focus | Completion criteria |
| --- | --- | --- |
| v0.1.x — Foundation | Structure, conventions, infrastructure, first adapters | Independent package builds, a working example, tests, and documentation |
| v0.2.x — Expansion | New AI/ML areas and compatibility | Adapters for validated tasks and checks against upstream |
| v0.3.x — Automation | Automatic configuration and validation | Transparent automated decisions with manual controls |
| v0.4.x — Integration | Cooperation between packages | Shared workflows that preserve package independence |
| v1.0.0 — Stable | Stability and broad adoption | Defined APIs, a compatibility policy, and complete documentation |

## Current foundation

- Two independently buildable packages: core and text.
- A shared error hierarchy and lazy backend loading.
- Working TF-IDF vectorization with vocabulary reuse.
- Tests, style checks, CI, and wheel/sdist builds.
- Package templates, a generator, and release conventions.

## Next decisions

The source repository is [knbww/pymplify](https://github.com/knbww/pymplify).
Before the first PyPI release, check distribution names, confirm CI results in
the repository, and validate dependency ranges.

Choose the next adapter based on a real task. Steering, image processing, neural
embeddings, and inference are possible directions without promised timelines.
Steering requires a separate choice of upstream library, supported models, dataset,
layer-selection rules, training resource requirements, and outcome validation.
