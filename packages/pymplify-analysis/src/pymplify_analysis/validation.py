"""Explicit, case-based comparison of original and candidate callables."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from pymplify_core import ConfigurationError


@dataclass(frozen=True)
class ValidationCase:
    """Representative inputs, copied separately for original and candidate execution."""

    name: str
    args: tuple[Any, ...] = ()
    kwargs: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ConfigurationError("Validation cases need a non-empty name.")
        try:
            args, kwargs = tuple(self.args), dict(self.kwargs)
        except (TypeError, ValueError) as exc:
            raise ConfigurationError(
                "Case args must be iterable and kwargs must be a mapping."
            ) from exc
        if not all(isinstance(name, str) for name in kwargs):
            raise ConfigurationError("Case keyword names must be strings.")
        object.__setattr__(self, "args", args)
        object.__setattr__(self, "kwargs", MappingProxyType(kwargs))


@dataclass(frozen=True)
class CaseResult:
    name: str
    passed: bool
    stage: str
    detail: str


@dataclass(frozen=True)
class ValidationReport:
    """Evidence for supplied cases only, never a general equivalence guarantee."""

    cases: tuple[CaseResult, ...]

    @property
    def passed(self) -> bool:
        return bool(self.cases) and all(case.passed for case in self.cases)


def validate_equivalence(
    original: Callable[..., Any],
    candidate: Callable[..., Any],
    cases: Iterable[ValidationCase],
    *,
    compare: Callable[[Any, Any], bool],
) -> ValidationReport:
    """Execute explicitly supplied callables and compare outputs on finite cases.

    Each invocation receives an independent deepcopy of the case inputs. A
    comparator is required because equality depends on the domain. Failures are
    recorded by stage; even matching exceptions are not considered successful
    output validation. Interruptions propagate. No source string is executed.
    """
    if not all(callable(item) for item in (original, candidate, compare)):
        raise ConfigurationError("original, candidate, and compare must be callable.")
    try:
        values = tuple(cases)
    except TypeError as exc:
        raise ConfigurationError(
            "cases must be a finite iterable of ValidationCase objects."
        ) from exc
    if not values or not all(isinstance(item, ValidationCase) for item in values):
        raise ConfigurationError("Provide at least one ValidationCase.")
    results: list[CaseResult] = []
    for case in values:
        stage = "copy-inputs"
        try:
            original_args, original_kwargs = deepcopy((case.args, dict(case.kwargs)))
            candidate_args, candidate_kwargs = deepcopy((case.args, dict(case.kwargs)))
            stage = "original"
            expected = original(*original_args, **original_kwargs)
            stage = "candidate"
            actual = candidate(*candidate_args, **candidate_kwargs)
            stage = "compare"
            passed = bool(compare(expected, actual))
            results.append(
                CaseResult(
                    case.name,
                    passed,
                    stage,
                    "Outputs match on this case." if passed else "Outputs differ.",
                )
            )
        except Exception as exc:
            # Explicit execution is opt-in. Preserve which step failed without
            # declaring two failing implementations behaviorally equivalent.
            results.append(CaseResult(case.name, False, stage, f"{type(exc).__name__}: {exc}"))
    return ValidationReport(tuple(results))
