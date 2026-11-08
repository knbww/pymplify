"""Inspect an example and explicitly compare a candidate on representative cases."""

from pathlib import Path

import numpy as np
from pymplify_analysis import ValidationCase, analyze_file, inspect_library, validate_equivalence
from pymplify_tabular import scale
from sklearn.preprocessing import StandardScaler


def main() -> None:
    source = Path(__file__).with_name("upstream_workflow.py")
    report = analyze_file(source)
    assert {item.rule for item in report.suggestions} >= {
        "text-fit-transform",
        "tabular-fit-transform",
    }
    for item in report.suggestions:
        print(item.title, "at line", item.locations[0].line)
        print(item.replacement)

    inventory = inspect_library("pymplify-analysis", max_files=20)
    assert inventory.functions and not inventory.issues
    print("Statically inspected definitions:", len(inventory.functions))

    def original(data):
        return StandardScaler().fit_transform(data)

    def candidate(data):
        return scale(data).data

    evidence = validate_equivalence(
        original,
        candidate,
        [
            ValidationCase("varying features", ([[1.0, 10.0], [2.0, 20.0], [3.0, 30.0]],)),
            ValidationCase("constant feature", ([[1.0, 2.0], [1.0, 4.0]],)),
        ],
        compare=lambda left, right: np.allclose(left, right, equal_nan=True),
    )
    assert evidence.passed
    print("Explicit comparison passed:", evidence.passed)


if __name__ == "__main__":
    main()
