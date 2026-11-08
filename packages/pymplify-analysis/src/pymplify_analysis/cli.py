"""Read-only text/JSON interface for source and library inspection."""

import argparse
import json
from dataclasses import asdict

from pymplify_core import ConfigurationError

from pymplify_analysis.analysis import analyze_file
from pymplify_analysis.inventory import inspect_library


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    code = commands.add_parser("code", help="Analyze a Python file without executing it.")
    code.add_argument("path")
    code.add_argument("--min-repetitions", type=int, default=2)
    library = commands.add_parser(
        "library", help="Inventory a local tree or installed distribution."
    )
    library.add_argument("target")
    library.add_argument("--max-files", type=int, default=100)
    library.add_argument("--include-private", action="store_true")
    for command in (code, library):
        command.add_argument("--json", action="store_true", dest="json_output")
        command.add_argument("--max-file-bytes", type=int, default=1_000_000)
    args = parser.parse_args(argv)
    try:
        if args.command == "code":
            report = analyze_file(
                args.path, min_repetitions=args.min_repetitions, max_file_bytes=args.max_file_bytes
            )
        else:
            report = inspect_library(
                args.target,
                max_files=args.max_files,
                max_file_bytes=args.max_file_bytes,
                include_private=args.include_private,
            )
    except ConfigurationError as exc:
        parser.error(str(exc))
    if args.json_output:
        print(json.dumps(asdict(report), indent=2, ensure_ascii=False, sort_keys=True))
    elif args.command == "code":
        print(f"{report.filename}: {len(report.suggestions)} unverified suggestion(s)")
        for item in report.suggestions:
            print(f"  line {item.locations[0].line}: [{item.rule}] {item.title}")
            print(f"    {item.explanation}")
            print("    Lines:", ", ".join(str(location.line) for location in item.locations))
            if item.requirements:
                print("    Requires:", ", ".join(item.requirements))
            if item.replacement:
                print(item.replacement)
            for caveat in item.caveats:
                print(f"    Review: {caveat}")
            for step in item.validation_steps:
                print(f"    Validate: {step}")
    else:
        print(
            f"{report.name}: {len(report.functions)} definition(s) in {len(report.files)} file(s)"
        )
        for function in report.functions:
            print(f"  {function.module}.{function.name}{function.signature}")
        print(f"Truncated: {report.truncated}")
        for issue in report.issues:
            print(f"  Issue: {issue.filename}: {issue.reason}")
    return 0
