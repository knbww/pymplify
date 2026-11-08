"""Create an independent package: python tools/new_package.py audio."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parents[1]


def create_package(name: str, *, root: Path = ROOT) -> Path:
    """Render a local scaffold; refuse invalid names or existing directories."""
    if re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", name) is None:
        raise ValueError("Use a lowercase name such as 'audio' or 'image-tools'.")
    distribution = f"pymplify-{name}"
    module = distribution.replace("-", "_")
    target = root / "packages" / distribution
    if target.exists():
        raise FileExistsError(f"Package already exists: {target}")

    # Read every input before writing, so a missing template cannot leave a partial scaffold.
    templates = root / "templates" / "package"
    context = {"name": name, "distribution": distribution, "module": module}
    files = {
        Path("pyproject.toml"): Template(
            (templates / "pyproject.toml.tmpl").read_text(encoding="utf-8")
        ).substitute(context),
        Path("README.md"): Template(
            (templates / "README.md.tmpl").read_text(encoding="utf-8")
        ).substitute(context),
        Path("LICENSE"): (root / "LICENSE").read_text(encoding="utf-8"),
        Path("src") / module / "__init__.py": Template(
            (templates / "__init__.py.tmpl").read_text(encoding="utf-8")
        ).substitute(context),
        Path("src") / module / "py.typed": "",
    }
    target.mkdir(parents=True, exist_ok=False)
    for relative_path, content in files.items():
        path = target / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="Direction name without the pymplify- prefix, e.g. audio")
    args = parser.parse_args()
    try:
        target = create_package(args.name)
    except (ValueError, FileExistsError) as exc:
        parser.error(str(exc))
    print(f"Created {target}")
    print("Next: add operations, an adapter factory, tests, documentation, and a CI entry.")


if __name__ == "__main__":
    main()
