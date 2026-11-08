"""Bounded inventories of Python definitions without importing target modules."""

from __future__ import annotations

import ast
import os
import sys
from importlib import metadata
from pathlib import Path

from pymplify_core import ConfigurationError

from pymplify_analysis.models import FileIssue, FunctionInfo, LibraryReport, Location
from pymplify_analysis.source import parse_source, positive_integer, read_source, render_expression

_EXCLUDED = {".git", ".tox", "node_modules", "build", "dist", "__pycache__", "tests", "test"}


def _source_files(root: Path, *, include_private: bool) -> list[Path]:
    if root.is_file():
        return [root] if root.suffix == ".py" and not root.is_symlink() else []
    result: list[Path] = []
    for directory, folders, files in os.walk(root, followlinks=False):
        folders[:] = sorted(
            name
            for name in folders
            if name not in _EXCLUDED
            and not name.startswith((".", "venv"))
            and (include_private or not name.startswith("_"))
        )
        for name in sorted(files):
            path = Path(directory) / name
            if (
                path.suffix == ".py"
                and not path.is_symlink()
                and (include_private or not name.startswith("_") or name == "__init__.py")
            ):
                result.append(path)
    return sorted(result)


def _installed_sources(name: str, *, include_private: bool) -> tuple[str, str, dict[Path, str]]:
    try:
        distribution = metadata.distribution(name)
    except metadata.PackageNotFoundError as original:
        matches = metadata.packages_distributions().get(name, [])
        if len(matches) != 1:
            raise ConfigurationError(
                f"Cannot resolve installed library '{name}'. Use an installed distribution name "
                "or a local Python file/directory; ambiguous import names need a distribution name."
            ) from original
        distribution = metadata.distribution(matches[0])
    paths: dict[Path, str] = {}
    for record in distribution.files or ():
        parts = record.parts
        if (
            record.suffix != ".py"
            or ".." in parts
            or any(
                part in _EXCLUDED or part.endswith((".dist-info", ".egg-info")) for part in parts
            )
        ):
            continue
        if not include_private and any(
            part.startswith("_") and part != "__init__.py" for part in parts
        ):
            continue
        path = Path(distribution.locate_file(record))
        if path.is_file() and not path.is_symlink():
            module_parts = record.with_suffix("").parts
            if module_parts[-1] == "__init__":
                module_parts = module_parts[:-1]
            paths[path] = ".".join(module_parts)
    # Editable installations often record only a .pth file and metadata. Locate
    # declared top-level packages on existing sys.path entries without find_spec:
    # resolving a dotted import with find_spec can execute a parent package.
    if not paths:
        for top_level in (distribution.read_text("top_level.txt") or "").splitlines():
            if not top_level.isidentifier():
                continue
            for entry in sys.path:
                base = Path(entry or os.curdir)
                for candidate in (base / top_level, base / f"{top_level}.py"):
                    if candidate.exists() and not candidate.is_symlink():
                        for path in _source_files(candidate, include_private=include_private):
                            relative = path.relative_to(base).with_suffix("")
                            parts = relative.parts
                            paths[path] = ".".join(parts[:-1] if parts[-1] == "__init__" else parts)
    return distribution.metadata["Name"], distribution.version, paths


def _definitions(
    tree: ast.Module,
    *,
    filename: str,
    module: str,
    include_private: bool,
) -> list[FunctionInfo]:
    result: list[FunctionInfo] = []

    def scan(statements: list[ast.stmt], prefix: str = "") -> None:
        for node in statements:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if not include_private and node.name.startswith("_"):
                continue
            name = f"{prefix}{node.name}"
            if isinstance(node, ast.ClassDef):
                scan(node.body, prefix=name + ".")
                continue
            signature = f"({render_expression(node.args)})"
            if node.returns is not None:
                signature += f" -> {render_expression(node.returns)}"
            docstring = ast.get_docstring(node) or ""
            result.append(
                FunctionInfo(
                    module=module,
                    name=name,
                    signature=signature,
                    summary=docstring.splitlines()[0][:500] if docstring else "",
                    location=Location(
                        filename, node.lineno, node.end_lineno or node.lineno, node.col_offset
                    ),
                    is_async=isinstance(node, ast.AsyncFunctionDef),
                )
            )

    scan(tree.body)
    return result


def inspect_library(
    target: str | Path,
    *,
    max_files: int = 100,
    max_file_bytes: int = 1_000_000,
    include_private: bool = False,
) -> LibraryReport:
    """Inventory local Python definitions or an installed distribution's source.

    Target modules, decorators, annotations, and default expressions are not
    executed. Returned definitions are syntactic, not guaranteed runtime exports.
    Native extensions, dynamic/re-exported APIs, and unavailable sources are not
    inferred. Partial results record file issues and truncation explicitly.
    """
    positive_integer(max_files, name="max_files")
    positive_integer(max_file_bytes, name="max_file_bytes")
    if not isinstance(target, (str, Path)) or not str(target).strip():
        raise ConfigurationError("target must name an installed distribution or a local path.")
    path = Path(target)
    if path.exists():
        if path.is_symlink():
            raise ConfigurationError("Inspect a concrete source path rather than a symbolic link.")
        name, version = str(path), None
        paths = _source_files(path, include_private=include_private)
        base = path if path.is_dir() else path.parent
    else:
        name, version, modules = _installed_sources(str(target), include_private=include_private)
        paths = sorted(modules)
        base = None
    functions: list[FunctionInfo] = []
    issues: list[FileIssue] = []
    selected = paths[:max_files]
    for source_path in selected:
        try:
            source = read_source(source_path, max_file_bytes=max_file_bytes)
            tree = parse_source(source, filename=str(source_path))
            if base is not None:
                parts = source_path.relative_to(base).with_suffix("").parts
                module = ".".join(parts[:-1] if parts[-1] == "__init__" else parts) or base.name
            else:
                module = modules[source_path]
            functions.extend(
                _definitions(
                    tree, filename=str(source_path), module=module, include_private=include_private
                )
            )
        except ConfigurationError as exc:
            issues.append(FileIssue(str(source_path), str(exc)))
    if not paths:
        issues.append(
            FileIssue(
                str(target),
                "No eligible Python sources found; native or dynamic APIs are not inspected.",
            )
        )
    return LibraryReport(
        name,
        version,
        tuple(str(item) for item in selected),
        tuple(functions),
        tuple(issues),
        len(paths) > max_files,
    )
