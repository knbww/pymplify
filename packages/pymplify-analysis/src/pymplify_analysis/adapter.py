"""Lightweight entry point for the optional analysis package."""

from pymplify_core import Adapter, Operation

from pymplify_analysis.analysis import analyze_code, analyze_file
from pymplify_analysis.inventory import inspect_library


def get_adapter() -> Adapter:
    return Adapter(
        name="analysis",
        library="python",
        aliases=("ast",),
        description="Static source inspection and explainable simplification proposals.",
        operations=(
            Operation(
                "analyze_code", analyze_code, "Inspect a source string without executing it."
            ),
            Operation("analyze_file", analyze_file, "Inspect a local Python file."),
            Operation(
                "inspect_library", inspect_library, "Inventory local or installed definitions."
            ),
        ),
    )
