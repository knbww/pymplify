# pymplify-analysis

Static Python source inspection and explainable simplification proposals. Python
3.10+, MIT. Depends only on `pymplify-core>=0.2.0,<0.3`; no ML runtime is required.

From the repository root:

```bash
python -m pip install -e ./packages/pymplify-core -e ./packages/pymplify-analysis
```

```python
from pymplify_analysis import analyze_code, inspect_library

report = analyze_code("""
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
scaled = scaler.fit_transform(data)
""")
for suggestion in report.suggestions:
    print(suggestion.explanation)
    print(suggestion.replacement)
    print(suggestion.validation_steps)

inventory = inspect_library("pymplify-analysis", max_files=20)
print(len(inventory.functions))
```

CLI equivalents:

```bash
python -m pymplify_analysis code examples/upstream_workflow.py --json
python -m pymplify_analysis library packages/pymplify-text/src --max-files 20
pymplify-analyze library scikit-learn --max-files 10 --json
```

Analysis reads AST and distribution metadata without importing or executing the
target library. It recognizes adjacent TF-IDF/scaler construction and
`fit_transform` calls, and repeated pairs of consecutive call names. Results
include locations, evidence, caveats, required packages, and validation steps.
Previews are unverified suggestions, not automatic patches. No files are changed.

`inspect_library` inventories syntactic definitions, including signatures,
first-line docstrings, and locations. Native extensions, dynamic exports,
re-exports, and runtime behavior are not inferred. File limits, oversized files,
and parse failures are reported explicitly. No online repositories are fetched.

`validate_equivalence` is a separate opt-in API that executes supplied callables
on explicit cases with an explicit comparator. Inputs are deep-copied separately;
passing cases provide bounded evidence rather than a universal equivalence proof.

Detailed reference: [analysis API](https://github.com/knbww/pymplify/blob/main/docs/analysis-api.md).
