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
            for package in ("pymplify-core", "pymplify-text")
        ),
    }
    code = """
import sys
import pymplify_core
import pymplify_text
assert 'sklearn' not in sys.modules
assert 'numpy' not in sys.modules
try:
    pymplify_text.vectorize(['example text'])
except pymplify_core.MissingDependencyError as exc:
    assert 'pip install' in str(exc)
    assert 'scikit-learn' in str(exc)
else:
    raise AssertionError('A backend should be missing under python -S')
"""
    result = subprocess.run(
        [sys.executable, "-S", "-c", code],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
