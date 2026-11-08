import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_packages_import_without_site_packages_and_missing_backend_is_actionable():
    env = {
        **os.environ,
        "PYTHONPATH": os.pathsep.join(
            str(ROOT / "packages" / package / "src")
            for package in (
                "pymplify-core",
                "pymplify-text",
                "pymplify-tabular",
                "pymplify-analysis",
            )
        ),
    }
    code = """
import sys
import pymplify_core
import pymplify_text
import pymplify_tabular
import pymplify_analysis
from pymplify_text.adapter import get_adapter as text_adapter
from pymplify_tabular.adapter import get_adapter as tabular_adapter
catalog = pymplify_core.Catalog([text_adapter(), tabular_adapter()])
assert len(catalog.for_library('sklearn')) == 2
assert pymplify_analysis.analyze_code('raise RuntimeError').suggestions == ()
assert 'sklearn' not in sys.modules
assert 'numpy' not in sys.modules
try:
    pymplify_text.vectorize(['example text'])
except pymplify_core.MissingDependencyError as exc:
    assert 'pip install' in str(exc)
    assert 'scikit-learn' in str(exc)
else:
    raise AssertionError('A backend should be missing under python -S')
try:
    pymplify_tabular.scale([[1, 2], [3, 4]])
except pymplify_core.MissingDependencyError:
    pass
else:
    raise AssertionError('The tabular backend should also be missing')
"""
    result = subprocess.run(
        [sys.executable, "-S", "-c", code],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_installed_discovery_does_not_import_ml_backends():
    code = """
import sys
from pymplify_core import discover_adapters
catalog = discover_adapters(strict=True)
assert {'analysis', 'text', 'tabular'} <= {adapter.name for adapter in catalog.adapters}
assert 'sklearn' not in sys.modules
assert 'numpy' not in sys.modules
assert 'scipy' not in sys.modules
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", code], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
