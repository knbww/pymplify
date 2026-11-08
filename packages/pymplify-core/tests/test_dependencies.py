from types import ModuleType

import pytest
from pymplify_core import (
    BackendError,
    ConfigurationError,
    MissingDependencyError,
    PymplifyError,
    require_dependency,
)


def test_imports_an_available_module():
    result = require_dependency("json", install="unused")
    assert isinstance(result, ModuleType)
    assert result.loads('{"value": 42}') == {"value": 42}


@pytest.mark.parametrize("missing", ["missing_backend", "missing_backend.adapter"])
def test_missing_backend_has_install_instruction_and_cause(monkeypatch, missing):
    error = ModuleNotFoundError("absent", name=missing)

    def unavailable(name):
        raise error

    monkeypatch.setattr("pymplify_core.dependencies.import_module", unavailable)
    with pytest.raises(MissingDependencyError, match='pip install "backend>=1,<2"') as caught:
        require_dependency("missing_backend.adapter", install="backend>=1,<2")
    assert caught.value.__cause__ is error


@pytest.mark.parametrize("missing", ["internal_dependency", None])
def test_broken_installation_is_not_reported_as_absent_backend(monkeypatch, missing):
    error = ModuleNotFoundError("backend installation is broken", name=missing)

    def broken(name):
        raise error

    monkeypatch.setattr("pymplify_core.dependencies.import_module", broken)
    with pytest.raises(ModuleNotFoundError) as caught:
        require_dependency("backend.adapter", install="backend")
    assert caught.value is error


def test_non_missing_import_errors_are_preserved(monkeypatch):
    error = ImportError("binary extension is incompatible")

    def broken(name):
        raise error

    monkeypatch.setattr("pymplify_core.dependencies.import_module", broken)
    with pytest.raises(ImportError) as caught:
        require_dependency("backend", install="backend")
    assert caught.value is error


@pytest.mark.parametrize(
    ("error_type", "builtin_type"),
    [
        (ConfigurationError, ValueError),
        (MissingDependencyError, ImportError),
        (BackendError, RuntimeError),
    ],
)
def test_errors_can_be_caught_by_ecosystem_or_builtin_type(error_type, builtin_type):
    error = error_type("details")
    assert isinstance(error, PymplifyError)
    assert isinstance(error, builtin_type)
