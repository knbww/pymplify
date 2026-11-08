import pytest
from pymplify_analysis import ValidationCase, ValidationReport, validate_equivalence
from pymplify_core import ConfigurationError


def compare(left, right):
    return left == right


def test_explicit_validation_compares_cases_and_independently_copies_mutable_inputs():
    data = [1, 2, 3]

    def original(values, *, multiplier):
        values.append(4)
        return sum(values) * multiplier

    def candidate(values, *, multiplier):
        return (sum(values) + 4) * multiplier

    cases = [ValidationCase("mutable inputs", (data,), {"multiplier": 2})]
    report = validate_equivalence(original, candidate, cases, compare=compare)
    assert report.passed and report.cases[0].passed
    assert data == [1, 2, 3]


def test_differences_are_evidence_not_success():
    report = validate_equivalence(
        lambda value: value,
        lambda value: value + 1,
        [ValidationCase("different", (1,))],
        compare=compare,
    )
    assert not report.passed
    assert report.cases[0].stage == "compare"
    assert report.cases[0].detail == "Outputs differ."
    assert not ValidationReport(()).passed


@pytest.mark.parametrize("stage", ["original", "candidate", "compare"])
def test_execution_and_comparator_errors_are_reported_by_stage(stage):
    def fail(*args):
        raise ValueError("specific failure")

    original = fail if stage == "original" else lambda value: value
    candidate = fail if stage == "candidate" else lambda value: value
    comparator = fail if stage == "compare" else compare
    report = validate_equivalence(
        original, candidate, [ValidationCase("failure", (1,))], compare=comparator
    )
    assert not report.passed
    assert report.cases[0].stage == stage
    assert "ValueError: specific failure" in report.cases[0].detail


def test_uncopyable_inputs_are_reported_without_executing_callbacks():
    class Uncopyable:
        def __deepcopy__(self, memo):
            raise TypeError("cannot copy")

    def never(value):
        pytest.fail("A callback must not run after copying failed")

    report = validate_equivalence(
        never, never, [ValidationCase("copy", (Uncopyable(),))], compare=compare
    )
    assert report.cases[0].stage == "copy-inputs"
    assert not report.passed


def test_matching_exceptions_are_not_a_successful_output_comparison():
    def fail():
        raise ValueError("same error")

    report = validate_equivalence(fail, fail, [ValidationCase("both fail")], compare=compare)
    assert not report.passed


def test_interruptions_propagate():
    def interrupted():
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        validate_equivalence(
            interrupted, interrupted, [ValidationCase("interrupt")], compare=compare
        )


@pytest.mark.parametrize("cases", [[], [object()], None])
def test_invalid_case_collections_are_rejected(cases):
    with pytest.raises(ConfigurationError):
        validate_equivalence(lambda: None, lambda: None, cases, compare=compare)


def test_invalid_callbacks_and_case_contracts_are_rejected():
    with pytest.raises(ConfigurationError, match="callable"):
        validate_equivalence(None, None, [ValidationCase("one")], compare=None)
    with pytest.raises(ConfigurationError, match="non-empty name"):
        ValidationCase("")
    with pytest.raises(ConfigurationError, match="iterable"):
        ValidationCase("bad", args=None)
    with pytest.raises(ConfigurationError, match="mapping"):
        ValidationCase("bad", kwargs=None)
    with pytest.raises(ConfigurationError, match="strings"):
        ValidationCase("bad", kwargs={1: "value"})


def test_case_snapshots_outer_collections():
    args, kwargs = [1], {"value": 2}
    case = ValidationCase("snapshot", args, kwargs)
    args.clear()
    kwargs.clear()
    assert case.args == (1,) and dict(case.kwargs) == {"value": 2}
