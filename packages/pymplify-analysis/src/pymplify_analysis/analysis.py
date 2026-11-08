"""Conservative AST rules for supported adapters and repeated call pairs."""

from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path

from pymplify_analysis.models import AnalysisReport, Location, Suggestion
from pymplify_analysis.source import parse_source, positive_integer, read_source, render_expression

_RULES = {
    "sklearn.feature_extraction.text.TfidfVectorizer": ("text", "vectorize", "matrix"),
    "sklearn.preprocessing.StandardScaler": ("tabular", "scale", "data"),
}


def _location(node: ast.AST, filename: str) -> Location:
    return Location(filename, node.lineno, node.end_lineno or node.lineno, node.col_offset)


def _dotted(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _dotted(node.value)
        return f"{parent}.{node.attr}" if parent else None
    return None


def _resolve(node: ast.AST, bindings: dict[str, str]) -> str | None:
    dotted = _dotted(node)
    if dotted is None:
        return None
    first, *rest = dotted.split(".")
    return ".".join((bindings.get(first, first), *rest))


def _assigned(node: ast.AST) -> set[str]:
    """Names potentially assigned in a statement; nested scopes are separate."""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return {node.name}
    return {
        item.id
        for item in ast.walk(node)
        if isinstance(item, ast.Name) and isinstance(item.ctx, (ast.Store, ast.Del))
    }


def _proposal(
    first: ast.stmt,
    second: ast.stmt,
    bindings: dict[str, str],
    source: str,
    filename: str,
    used_names: set[str],
) -> Suggestion | None:
    if not (
        isinstance(first, ast.Assign)
        and len(first.targets) == 1
        and isinstance(first.targets[0], ast.Name)
        and isinstance(first.value, ast.Call)
    ):
        return None
    constructor = first.value
    dotted_constructor = _dotted(constructor.func)
    if dotted_constructor is None or dotted_constructor.split(".")[0] not in bindings:
        return None
    qualified = _resolve(constructor.func, bindings)
    if (
        qualified not in _RULES
        or constructor.args
        or any(k.arg is None for k in constructor.keywords)
    ):
        return None
    if not (
        isinstance(second, ast.Assign)
        and len(second.targets) == 1
        and isinstance(second.targets[0], ast.Name)
        and isinstance(second.value, ast.Call)
    ):
        return None
    fit = second.value
    model_name = first.targets[0].id
    if not (
        isinstance(fit.func, ast.Attribute)
        and isinstance(fit.func.value, ast.Name)
        and fit.func.value.id == model_name
        and fit.func.attr == "fit_transform"
        and len(fit.args) == 1
        and not fit.keywords
        and not isinstance(fit.args[0], ast.Starred)
    ):
        return None
    # Resolving the constructor through its own result name would be ambiguous.
    if dotted_constructor.split(".")[0] == model_name:
        return None
    adapter, operation, field = _RULES[qualified]
    result_name = "_pymplify_result"
    while result_name in used_names:
        result_name += "_"
    arguments = [render_expression(fit.args[0])]
    arguments.extend(f"{item.arg}={render_expression(item.value)}" for item in constructor.keywords)
    replacement = (
        f"from pymplify_{adapter} import {operation}\n\n"
        f"{result_name} = {operation}({', '.join(arguments)})\n"
        f"{model_name} = {result_name}.model\n"
        f"{second.targets[0].id} = {result_name}.{field}"
    )
    caveats = [
        "This preview is not an automatic patch or a proof of equivalence.",
        "Review argument order, variable bindings, import names, and exception handling.",
        "The preview preserves the fitted model and output; it may not reduce the line count.",
    ]
    if adapter == "text":
        caveats.append("vectorize requires a finite ordered iterable of non-empty strings.")
    return Suggestion(
        rule=f"{adapter}-fit-transform",
        title=f"Use the {adapter}.{operation} adapter",
        explanation=(
            f"Adjacent {qualified} construction and fit_transform match a supported workflow."
        ),
        locations=(_location(first, filename), _location(second, filename)),
        original="\n".join(source.splitlines()[first.lineno - 1 : second.end_lineno]),
        replacement=replacement,
        requirements=(f"pymplify-{adapter}", "scikit-learn>=1.4.2,<2"),
        caveats=tuple(caveats),
        validation_steps=(
            "Compare native output types, shapes, and numerical values on representative inputs.",
            "Compare fitted state and transformations of unseen samples without refitting.",
            "Check empty, invalid, sparse, and task-specific inputs and expected exceptions.",
            "Use validate_equivalence with an explicit comparator before adopting the candidate.",
        ),
    )


def _direct_call(statement: ast.stmt) -> ast.Call | None:
    value = getattr(statement, "value", None)
    return value if isinstance(value, ast.Call) else None


def analyze_code(
    source: str,
    *,
    filename: str = "<string>",
    min_repetitions: int = 2,
) -> AnalysisReport:
    """Inspect Python source without executing it. Proposals remain unverified.

    Recognizes adjacent constructor/fit_transform calls for two known backends,
    and repeated pairs of consecutive direct calls. Import aliases and obvious
    shadowing are tracked; dynamic behavior is outside static rule guarantees.
    """
    positive_integer(min_repetitions, name="min_repetitions", minimum=2)
    tree = parse_source(source, filename=filename)
    suggestions: list[Suggestion] = []
    imports: set[str] = set()
    pairs: dict[tuple[str, str], list[tuple[ast.stmt, ast.stmt]]] = defaultdict(list)
    used_names = {item.id for item in ast.walk(tree) if isinstance(item, ast.Name)}

    def scan(statements: list[ast.stmt], inherited: dict[str, str]) -> None:
        bindings = inherited.copy()
        previous: tuple[ast.stmt, str] | None = None
        last_pair_end: dict[tuple[str, str], int] = {}
        for index, statement in enumerate(statements):
            if index + 1 < len(statements):
                candidate = _proposal(
                    statement, statements[index + 1], bindings, source, filename, used_names
                )
                if candidate is not None:
                    suggestions.append(candidate)
            call = _direct_call(statement)
            name = _resolve(call.func, bindings) if call is not None else None
            if previous is not None and name is not None:
                key = (previous[1], name)
                if any("." in part for part in key) and last_pair_end.get(key, -1) < index - 1:
                    pairs[key].append((previous[0], statement))
                    last_pair_end[key] = index
            previous = (statement, name) if name is not None else None

            if isinstance(statement, ast.Import):
                for item in statement.names:
                    imports.add(item.name)
                    bindings[item.asname or item.name.split(".")[0]] = (
                        item.name if item.asname else item.name.split(".")[0]
                    )
            elif isinstance(statement, ast.ImportFrom):
                module = "." * statement.level + (statement.module or "")
                imports.add(module)
                for item in statement.names:
                    if item.name == "*":
                        bindings.clear()
                    else:
                        bindings[item.asname or item.name] = f"{module}.{item.name}"
            else:
                child_bindings = bindings.copy()
                for name in _assigned(statement):
                    bindings.pop(name, None)
                if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for item in ast.walk(statement.args):
                        if isinstance(item, ast.arg):
                            child_bindings.pop(item.arg, None)
                    for child in statement.body:
                        for name in _assigned(child):
                            child_bindings.pop(name, None)
                elif isinstance(statement, (ast.For, ast.AsyncFor, ast.With, ast.AsyncWith)):
                    targets = (
                        [statement.target]
                        if isinstance(statement, (ast.For, ast.AsyncFor))
                        else [
                            item.optional_vars
                            for item in statement.items
                            if item.optional_vars is not None
                        ]
                    )
                    for target in targets:
                        for name in _assigned(target):
                            child_bindings.pop(name, None)
                # Analyze each nested statement-list separately, never joining
                # branches or function bodies into one consecutive workflow.
                for _, value in ast.iter_fields(statement):
                    if (
                        isinstance(value, list)
                        and value
                        and all(isinstance(x, ast.stmt) for x in value)
                    ):
                        scan(value, child_bindings)
                    elif isinstance(value, list):
                        for child in value:
                            if isinstance(child, ast.ExceptHandler):
                                scan(child.body, {})

    scan(tree.body, {})
    for names, occurrences in pairs.items():
        if len(occurrences) < min_repetitions:
            continue
        locations = tuple(
            Location(filename, first.lineno, second.end_lineno or second.lineno, first.col_offset)
            for first, second in occurrences
        )
        suggestions.append(
            Suggestion(
                rule="repeated-call-pair",
                title=f"Review repeated workflow: {' → '.join(names)}",
                explanation=(
                    f"The same pair of direct call names occurs {len(occurrences)} times "
                    "in separate non-overlapping spans."
                ),
                locations=locations,
                original="\n".join(
                    source.splitlines()[locations[0].line - 1 : locations[0].end_line]
                ),
                replacement=None,
                requirements=(),
                caveats=(
                    "Matching names do not prove matching inputs, receivers, state, or semantics.",
                    "Review whether these calls belong in a function or custom Adapter operation.",
                ),
                validation_steps=(
                    "Identify inputs, outputs, side effects, and errors at each occurrence.",
                    "Extract a candidate and compare it on cases covering all occurrences.",
                ),
            )
        )
    return AnalysisReport(
        filename,
        tuple(sorted(imports)),
        tuple(sorted(suggestions, key=lambda item: (item.locations[0].line, item.rule))),
    )


def analyze_file(
    path: str | Path,
    *,
    min_repetitions: int = 2,
    max_file_bytes: int = 1_000_000,
) -> AnalysisReport:
    """Read one Python file with its declared encoding, bounded by byte size."""
    path = Path(path)
    return analyze_code(
        read_source(path, max_file_bytes=max_file_bytes),
        filename=str(path),
        min_repetitions=min_repetitions,
    )
