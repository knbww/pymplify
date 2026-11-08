import importlib.util
import shutil
from pathlib import Path

import pytest

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("new_package", ROOT / "tools" / "new_package.py")
new_package = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(new_package)


@pytest.fixture
def scaffold_root(tmp_path):
    shutil.copytree(ROOT / "templates", tmp_path / "templates")
    shutil.copyfile(ROOT / "LICENSE", tmp_path / "LICENSE")
    return tmp_path


def test_scaffold_creates_an_independent_package_with_valid_metadata(scaffold_root):
    target = new_package.create_package("image-tools", root=scaffold_root)
    metadata = tomllib.loads((target / "pyproject.toml").read_text(encoding="utf-8"))
    assert metadata["project"]["name"] == "pymplify-image-tools"
    assert metadata["project"]["dependencies"] == ["pymplify-core>=0.2.0,<0.3"]
    assert (target / "src" / "pymplify_image_tools" / "py.typed").exists()
    assert (target / "LICENSE").read_bytes() == (ROOT / "LICENSE").read_bytes()


@pytest.mark.parametrize("name", ["../escape", "Audio", "audio_tools", "", "audio/tools"])
def test_invalid_names_cannot_escape_packages_directory(scaffold_root, name):
    with pytest.raises(ValueError, match="lowercase"):
        new_package.create_package(name, root=scaffold_root)
    assert not (scaffold_root / "packages").exists()


def test_scaffold_refuses_to_overwrite_existing_work(scaffold_root):
    target = new_package.create_package("audio", root=scaffold_root)
    readme = target / "README.md"
    readme.write_text("existing work", encoding="utf-8")
    with pytest.raises(FileExistsError):
        new_package.create_package("audio", root=scaffold_root)
    assert readme.read_text(encoding="utf-8") == "existing work"
