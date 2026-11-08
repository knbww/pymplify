"""Immutable, JSON-serializable evidence from static analysis."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    """One-based source lines; columns use Python AST's zero-based byte offsets."""

    filename: str
    line: int
    end_line: int
    column: int = 0


@dataclass(frozen=True)
class FunctionInfo:
    """A syntactic function definition, not a guarantee of a runtime public API."""

    module: str
    name: str
    signature: str
    summary: str
    location: Location
    is_async: bool


@dataclass(frozen=True)
class Suggestion:
    """An unverified proposal with evidence, caveats, and concrete validation steps."""

    rule: str
    title: str
    explanation: str
    locations: tuple[Location, ...]
    original: str
    replacement: str | None
    requirements: tuple[str, ...]
    caveats: tuple[str, ...]
    validation_steps: tuple[str, ...]
    validated: bool = False


@dataclass(frozen=True)
class AnalysisReport:
    """Imports and proposals found without executing source or importing its modules."""

    filename: str
    imports: tuple[str, ...]
    suggestions: tuple[Suggestion, ...]


@dataclass(frozen=True)
class FileIssue:
    """A source file or distribution that could not be fully inspected."""

    filename: str
    reason: str


@dataclass(frozen=True)
class LibraryReport:
    """Bounded static inventory of a local tree or installed distribution."""

    name: str
    version: str | None
    files: tuple[str, ...]
    functions: tuple[FunctionInfo, ...]
    issues: tuple[FileIssue, ...]
    truncated: bool
