import sys
from importlib import metadata
from pathlib import Path
from types import SimpleNamespace

import pytest
from pymplify_analysis import inspect_library
from pymplify_core import ConfigurationError


def fake_distribution(root, *, files=(), top_level="", name="sample-library"):
    return SimpleNamespace(
        metadata={"Name": name},
        version="1.2.3",
        files=[metadata.PackagePath(item) for item in files],
        locate_file=lambda record: root / record,
        read_text=lambda filename: top_level if filename == "top_level.txt" else None,
    )


def test_local_inventory_extracts_signatures_methods_async_and_docs_without_execution(tmp_path):
    path = tmp_path / "module.py"
    marker = tmp_path / "executed"
    path.write_text(
        f'''
raise RuntimeError("must not execute")
def public(value: int = dangerous(), /, *, flag=True) -> str:
    """A useful function.

    More detail.
    """
    def nested():
        pass
    return str(value)
def _private():
    pass
class Service:
    async def run(self, value):
        return value
    def _internal(self):
        pass
class _Hidden:
    def visible_name(self):
        pass
open({str(marker)!r}, "w").write("bad")
''',
        encoding="utf-8",
    )
    report = inspect_library(tmp_path)
    assert [item.name for item in report.functions] == ["public", "Service.run"]
    function = report.functions[0]
    assert function.module == "module"
    assert "dangerous()" in function.signature and "-> str" in function.signature
    assert function.summary == "A useful function."
    assert report.functions[1].is_async
    assert report.files == (str(path),)
    assert not report.truncated and not report.issues
    assert not marker.exists()
    private = inspect_library(tmp_path, include_private=True)
    assert {"_private", "Service._internal", "_Hidden.visible_name"} <= {
        item.name for item in private.functions
    }


def test_file_limits_private_modules_and_excluded_trees_are_explicit(tmp_path):
    for name in ["a.py", "b.py", "_private.py"]:
        (tmp_path / name).write_text("def operation(): pass", encoding="utf-8")
    for folder in ["tests", ".venv", "build", "_internal"]:
        (tmp_path / folder).mkdir()
        (tmp_path / folder / "hidden.py").write_text("def hidden(): pass", encoding="utf-8")
    report = inspect_library(tmp_path, max_files=1)
    assert report.truncated and len(report.files) == 1
    assert len(inspect_library(tmp_path).files) == 2
    assert len(inspect_library(tmp_path, include_private=True).files) == 4


def test_syntax_size_and_encoding_failures_do_not_discard_other_files(tmp_path):
    (tmp_path / "a.py").write_text("def broken(:", encoding="utf-8")
    (tmp_path / "b.py").write_text("# padding\n" * 100, encoding="utf-8")
    (tmp_path / "c.py").write_bytes(b"# coding: not-a-real-encoding\n")
    (tmp_path / "d.py").write_text("def good(): pass", encoding="utf-8")
    report = inspect_library(tmp_path, max_file_bytes=100)
    assert [item.name for item in report.functions] == ["good"]
    assert len(report.issues) == 3
    assert any("exceeds" in item.reason for item in report.issues)


def test_excessively_nested_signatures_are_reported_as_file_issues(tmp_path):
    expression = " + ".join(["1"] * 2000)
    (tmp_path / "nested.py").write_text(
        f"def operation(value={expression}): pass", encoding="utf-8"
    )
    report = inspect_library(tmp_path)
    assert not report.functions and report.issues


def test_installed_distribution_uses_recorded_sources_and_keeps_full_module_names(
    tmp_path, monkeypatch
):
    package = tmp_path / "sample"
    package.mkdir()
    (package / "api.py").write_text("def predict(value): return value", encoding="utf-8")
    distribution = fake_distribution(
        tmp_path, files=["sample/api.py", "sample/_private.py", "../outside.py", "native.so"]
    )
    monkeypatch.setattr(
        "pymplify_analysis.inventory.metadata.distribution", lambda name: distribution
    )
    report = inspect_library("sample-library")
    assert report.name == "sample-library" and report.version == "1.2.3"
    assert report.functions[0].module == "sample.api"
    assert not report.issues


def test_import_alias_can_resolve_a_single_distribution(tmp_path, monkeypatch):
    path = tmp_path / "sample.py"
    path.write_text("def predict(): pass", encoding="utf-8")
    distribution = fake_distribution(tmp_path, files=["sample.py"])

    def resolve(name):
        if name == "sample":
            raise metadata.PackageNotFoundError(name)
        return distribution

    monkeypatch.setattr("pymplify_analysis.inventory.metadata.distribution", resolve)
    monkeypatch.setattr(
        "pymplify_analysis.inventory.metadata.packages_distributions",
        lambda: {"sample": ["sample-library"]},
    )
    assert inspect_library("sample").name == "sample-library"


def test_editable_sources_are_located_without_importing_the_package(tmp_path, monkeypatch):
    root = tmp_path / "editable"
    root.mkdir()
    (root / "__init__.py").write_text("raise RuntimeError('must not execute')", encoding="utf-8")
    (root / "api.py").write_text("def public(): pass", encoding="utf-8")
    distribution = fake_distribution(
        tmp_path, files=["editable.pth"], top_level="../escape\neditable\n"
    )
    monkeypatch.setattr(
        "pymplify_analysis.inventory.metadata.distribution", lambda name: distribution
    )
    monkeypatch.setattr(sys, "path", [str(tmp_path)])
    report = inspect_library("sample-library")
    assert report.functions[0].module == "editable.api"
    assert "editable" not in sys.modules


@pytest.mark.parametrize("matches", [[], ["first", "second"]])
def test_unknown_or_ambiguous_names_have_actionable_errors(monkeypatch, matches):
    def missing(name):
        raise metadata.PackageNotFoundError(name)

    monkeypatch.setattr("pymplify_analysis.inventory.metadata.distribution", missing)
    monkeypatch.setattr(
        "pymplify_analysis.inventory.metadata.packages_distributions", lambda: {"missing": matches}
    )
    with pytest.raises(ConfigurationError, match="Cannot resolve installed library"):
        inspect_library("missing")


def test_no_python_sources_is_reported_instead_of_inventing_a_runtime_api(tmp_path, monkeypatch):
    distribution = fake_distribution(tmp_path, files=["native.so"])
    monkeypatch.setattr(
        "pymplify_analysis.inventory.metadata.distribution", lambda name: distribution
    )
    report = inspect_library("sample-library")
    assert not report.functions and report.issues
    assert "native or dynamic APIs" in report.issues[0].reason
    (tmp_path / "native.so").write_bytes(b"native-extension-placeholder")
    assert inspect_library(tmp_path / "native.so").issues


def test_explicit_symlink_roots_are_rejected_and_symlink_files_are_skipped(tmp_path):
    source = tmp_path / "source.py"
    source.write_text("def operation(): pass", encoding="utf-8")
    link = tmp_path / "link.py"
    try:
        link.symlink_to(source)
    except OSError:
        pytest.skip("Symlinks are unavailable on this platform.")
    with pytest.raises(ConfigurationError, match="symbolic link"):
        inspect_library(link)
    assert inspect_library(tmp_path).files == (str(source),)


@pytest.mark.parametrize("target", [None, "", " "])
def test_invalid_targets_are_rejected(target):
    with pytest.raises(ConfigurationError, match="target"):
        inspect_library(target)


@pytest.mark.parametrize("options", [{"max_files": 0}, {"max_file_bytes": False}])
def test_invalid_limits_are_rejected(options):
    with pytest.raises(ConfigurationError):
        inspect_library(Path(__file__), **options)
