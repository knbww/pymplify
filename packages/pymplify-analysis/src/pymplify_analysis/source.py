"""Source loading and parsing; no eval, execution, or target-module imports."""

import ast
import tokenize
from pathlib import Path

from pymplify_core import ConfigurationError


def positive_integer(value: int, *, name: str, minimum: int = 1) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ConfigurationError(f"{name} must be an integer >= {minimum}.")


def read_source(path: Path, *, max_file_bytes: int) -> str:
    positive_integer(max_file_bytes, name="max_file_bytes")
    try:
        if path.stat().st_size > max_file_bytes:
            raise ConfigurationError(f"{path}: source exceeds max_file_bytes={max_file_bytes}.")
        with tokenize.open(path) as stream:
            return stream.read()
    except (OSError, UnicodeError, SyntaxError) as exc:
        raise ConfigurationError(f"Cannot read Python source {path}: {exc}") from exc


def parse_source(source: str, *, filename: str) -> ast.Module:
    if not isinstance(source, str):
        raise ConfigurationError("source must be a Python source string.")
    try:
        return ast.parse(source, filename=filename)
    except (SyntaxError, ValueError, RecursionError) as exc:
        raise ConfigurationError(f"Cannot parse {filename}: {exc}") from exc


def render_expression(node: ast.AST) -> str:
    """Format parsed expressions while reporting unsupported nesting cleanly."""
    try:
        return ast.unparse(node)
    except RecursionError as exc:
        raise ConfigurationError(
            "Expression nesting exceeds the static formatter's limit."
        ) from exc
