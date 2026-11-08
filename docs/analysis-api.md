# Static analysis and candidate validation

`pymplify-analysis` is an optional Python 3.10+ package that depends only on core.
It keeps three activities separate: static source inspection, unverified
simplification proposals, and explicitly requested execution-based validation.

## Source analysis

```python
from pymplify_analysis import analyze_code, analyze_file

report = analyze_code(
    """
from sklearn.feature_extraction.text import TfidfVectorizer as TF
vectorizer = TF(max_features=100)
matrix = vectorizer.fit_transform(documents)
""",
    filename="workflow.py",
)
for item in report.suggestions:
    print(item.rule, item.locations, item.explanation)
    print(item.replacement)
    print(item.caveats, item.validation_steps)

file_report = analyze_file("examples/upstream_workflow.py")
```

| API | Result |
| --- | --- |
| `analyze_code(source, *, filename="<string>", min_repetitions=2)` | An `AnalysisReport` containing imports and a tuple of proposals |
| `analyze_file(path, *, min_repetitions=2, max_file_bytes=1_000_000)` | The same report after a size-bounded read respecting Python encoding declarations |
| `inspect_library(target, *, max_files=100, max_file_bytes=1_000_000, include_private=False)` | A `LibraryReport` containing source definitions and inspection issues |
| `validate_equivalence(original, candidate, cases, *, compare)` | A `ValidationReport` for explicitly executed callables and supplied cases |

An `AnalysisReport` has `filename`, sorted `imports`, and `suggestions` ordered by
source location. Each `Suggestion` contains a stable rule identifier, title,
explanation, locations, original source, optional replacement preview, required
packages, caveats, validation steps, and `validated=False`.

Locations use one-based lines and zero-based AST byte columns. `original` includes
the matched source lines; previews are new snippets, not source-preserving edits.
Passing a validation report does not mutate a suggestion or claim a general proof.

### Implemented rules

- `text-fit-transform`: adjacent assignments constructing an imported
  `sklearn.feature_extraction.text.TfidfVectorizer` and calling its
  `fit_transform(documents)`; proposes `pymplify_text.vectorize`.
- `tabular-fit-transform`: the corresponding `StandardScaler` pattern; proposes
  `pymplify_tabular.scale`.
- `repeated-call-pair`: the same pair of consecutive direct call names appears in
  at least `min_repetitions` non-overlapping spans; proposes reviewing a reusable
  function or custom operation, without inventing executable replacement code.

Known-workflow rules require an explicit resolvable import, one model assignment,
one output assignment, no positional constructor arguments, no `**options`, and
exactly one positional fit argument. Import aliases and obvious assignments,
parameters, loop targets, and context-manager targets that shadow imports are
handled conservatively. Wildcard imports invalidate known bindings. Branches and
function bodies are scanned separately, never joined into a consecutive workflow.

These are bounded syntactic rules. Runtime monkeypatching, dynamic imports,
reflection, receiver identity, side effects, and complete Python data flow are
not inferred. Name repetition does not establish semantic equivalence.

Known previews retain fitted-model and output variable bindings, using an extra
result variable. This may add lines while simplifying access to a supported
workflow. Review argument evaluation order, imports, exceptions, and name binding
before use. TF-IDF proposals also require the adapter's finite ordered non-empty
string inputs; the adapter rejects some inputs the original backend accepts.

No source is executed or modified during analysis. No packages are installed,
GitHub repositories fetched, or external model services called.

## Library inventory

```python
from pymplify_analysis import inspect_library

inventory = inspect_library("pymplify-analysis", max_files=20)
local = inspect_library("packages/pymplify-text/src", include_private=True)
for item in inventory.functions:
    print(item.module, item.name, item.signature, item.summary, item.location)
for issue in inventory.issues:
    print(issue.filename, issue.reason)
print(inventory.truncated)
```

An existing file or directory is inspected locally. Otherwise the target is
resolved using installed distribution metadata. Import names are accepted only
when they identify one distribution; ambiguous names require the distribution
name. Missing targets raise `ConfigurationError` with resolution guidance.

Recorded `.py` files are read without importing target modules. For simple
editable installs without recorded sources, declared top-level packages are
located on existing `sys.path` entries. Arbitrary executable `.pth` contents and
custom import loaders are not evaluated; unsupported layouts can yield no sources.

The report contains `name`, optional installed `version`, selected `files`,
`functions`, per-file `issues`, and `truncated`. Definitions include direct
module-level functions and class methods, signatures, async flags, first-line
docstrings capped at 500 characters, and locations. Local module names are
relative to the inspected root; installed records preserve package-qualified names.

This is a source inventory, not a runtime export list. Nested local functions,
conditional definitions, re-exports, generated objects, native extensions, and
dynamic APIs are not reconstructed. Private names are omitted unless requested.
Repository caches, build output, virtual environments, and test trees are excluded;
symbolic links are skipped and explicit symlink roots are rejected.

`max_files` bounds parsed files, not the enumeration of directory entries or
distribution metadata. Oversized, unreadable, undecodable, and syntactically
invalid files are reported without discarding other results. `truncated=True`
means eligible files remain beyond the selected limit. No eligible source files
produces an explicit issue rather than an invented API inventory.

## Explicit candidate validation

```python
from pymplify_analysis import ValidationCase, validate_equivalence

original = lambda values: sum(values)
candidate = lambda values: sum(value for value in values)
report = validate_equivalence(
    original,
    candidate,
    [ValidationCase("positive values", ([1, 2, 3],)), ValidationCase("empty values", ([],))],
    compare=lambda expected, actual: expected == actual,
)
assert report.passed
```

Unlike static analysis, this API executes the two supplied callables and comparator
normally. It never executes source strings or automatically runs a preview.
Use only callables you intend to run; copying inputs does not isolate global state,
filesystem effects, network activity, or custom object behavior.

`ValidationCase(name, args=(), kwargs={})` snapshots its outer input collections.
Before each invocation the case inputs are deep-copied separately, preserving
input sharing within each invocation. Choose a comparator appropriate to your
domain: sparse/dense types, numerical tolerances, fitted state, and unseen-sample
behavior need deliberate checks. A comparator must return a boolean-compatible
result; an ambiguous array or comparator exception fails the case.

The report contains `cases`, each with `name`, `passed`, `stage`, and `detail`.
Stages identify input copying, original execution, candidate execution, or output
comparison. An exception fails the case, even when both implementations might
raise the same exception. Empty case collections and invalid contracts are
rejected. Interruptions propagate. `report.passed` means all supplied cases passed;
it says nothing about untested inputs or global equivalence.

Generated previews are tested against original scikit-learn workflows using trusted
fixtures, including output values, fitted-model parameters, and unseen inputs.
Applications must still validate their own data and assumptions. See the
[runnable example](../examples/analyze_workflows.py) for numerical comparison.

## CLI and catalog integration

```bash
python -m pymplify_analysis code examples/upstream_workflow.py --json
pymplify-analyze code examples/upstream_workflow.py --min-repetitions 3
python -m pymplify_analysis library pymplify-analysis --max-files 20 --json
```

Both entry points support text or JSON reports. The code command accepts
`--min-repetitions`; library accepts `--max-files` and `--include-private`; both
accept `--max-file-bytes`. Text output includes caveats and validation steps.
Configuration/read/parse failures exit with status 2. Partial library inventories
exit with status 0 and expose their issues and truncation in the report.

The installed distribution advertises adapter `analysis`, library `python`, alias
`ast`, and operations `analyze_code`, `analyze_file`, and `inspect_library`.
The execution-based validator is intentionally not invoked during discovery or
static analysis. Existing core/text/tabular versions remain independent.

References: [Python AST](https://docs.python.org/3.10/library/ast.html),
[distribution metadata](https://docs.python.org/3.10/library/importlib.metadata.html),
[source encodings](https://docs.python.org/3.10/library/tokenize.html).
