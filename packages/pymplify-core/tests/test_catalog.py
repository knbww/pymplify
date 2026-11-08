import sys
from dataclasses import FrozenInstanceError
from importlib.metadata import EntryPoint
from types import ModuleType

import pytest
from pymplify_core import (
    Adapter,
    AdapterLoadError,
    AdapterNotFoundError,
    Catalog,
    ConfigurationError,
    Operation,
    OperationNotFoundError,
    discover_adapters,
)


def make_adapter(name="text"):
    return Adapter(
        name=name,
        library="scikit-learn",
        operations=(Operation("identity", lambda value: value, "Return the original value."),),
        aliases=("sklearn",),
    )


def install_entry(monkeypatch, *, name="text", factory=None, module="test_pymplify_plugin"):
    plugin = ModuleType(module)
    plugin.factory = factory or make_adapter
    monkeypatch.setitem(sys.modules, module, plugin)
    return EntryPoint(name=name, value=f"{module}:factory", group="pymplify.adapters")


def set_entries(monkeypatch, *entries):
    def installed(*, group):
        assert group == "pymplify.adapters"
        return entries

    monkeypatch.setattr("pymplify_core.catalog.entry_points", installed)


def test_custom_operation_preserves_native_objects_and_all_keyword_arguments():
    result = object()

    def custom(*, adapter, operation, self):
        assert (adapter, operation, self) == ("upstream", "predict", 42)
        return result

    adapter = Adapter("custom", "my-library", (Operation("run", custom),))
    catalog = Catalog([adapter])
    assert catalog.run("custom", "run", adapter="upstream", operation="predict", self=42) is result


def test_operation_failure_is_not_reclassified_as_discovery_failure():
    error = ValueError("original operation failed")

    def fail():
        raise error

    catalog = Catalog([Adapter("custom", "library", (Operation("fail", fail),))])
    with pytest.raises(ValueError) as caught:
        catalog.run("custom", "fail")
    assert caught.value is error


def test_catalog_lists_without_running_operations_and_normalizes_library_names():
    adapter = make_adapter()
    catalog = Catalog([adapter])
    assert catalog.adapters == (adapter,)
    assert catalog.for_library(" SciKit_Learn ") == (adapter,)
    assert catalog.for_library("sklearn") == (adapter,)
    assert catalog.for_library("unsupported-library") == ()
    assert catalog.get("text").operation("identity").description == "Return the original value."


def test_adapters_are_sorted_and_registration_is_local():
    first = Catalog([make_adapter("zeta"), make_adapter("alpha")])
    second = Catalog()
    assert [item.name for item in first.adapters] == ["alpha", "zeta"]
    assert second.adapters == ()
    assert second.discovery_issues == ()


def test_duplicate_registration_cannot_replace_existing_adapter():
    original = make_adapter()
    catalog = Catalog([original])
    with pytest.raises(ConfigurationError, match="already registered"):
        catalog.register(make_adapter())
    assert catalog.get("text") is original


def test_register_requires_the_public_adapter_contract():
    with pytest.raises(ConfigurationError, match="Adapter instance"):
        Catalog().register(object())


def test_unknown_adapter_and_operation_errors_explain_available_choices():
    with pytest.raises(AdapterNotFoundError, match="Available: none"):
        Catalog().get("missing")
    catalog = Catalog([make_adapter()])
    with pytest.raises(AdapterNotFoundError, match="Available: text"):
        catalog.run("missing", "identity", 1)
    with pytest.raises(OperationNotFoundError, match="Available: identity"):
        catalog.run("text", "missing", 1)


def test_contract_snapshots_mutable_collections():
    operations = [Operation("identity", lambda value: value)]
    aliases = ["sklearn"]
    adapter = Adapter("text", "scikit-learn", operations, aliases=aliases)
    operations.clear()
    aliases.clear()
    assert len(adapter.operations) == 1
    assert adapter.aliases == ("sklearn",)
    with pytest.raises(FrozenInstanceError):
        adapter.name = "changed"


@pytest.mark.parametrize("name", ["", "Bad Name", "../escape", 12])
def test_invalid_identifiers_are_rejected(name):
    with pytest.raises(ConfigurationError, match="lowercase identifier"):
        Operation(name, lambda: None)
    with pytest.raises(ConfigurationError, match="lowercase identifier"):
        make_adapter(name)


@pytest.mark.parametrize("name", ["", "  ", None])
def test_invalid_library_names_are_rejected(name):
    with pytest.raises(ConfigurationError, match="non-empty strings"):
        Adapter("custom", name, (Operation("run", lambda: None),))
    with pytest.raises(ConfigurationError, match="non-empty strings"):
        Catalog().for_library(name)


def test_invalid_operation_contract_is_rejected():
    with pytest.raises(ConfigurationError, match="callable"):
        Operation("run", 42)
    with pytest.raises(ConfigurationError, match="description must be a string"):
        Operation("run", lambda: None, description=None)


@pytest.mark.parametrize("operations", [(), (object(),), None])
def test_empty_or_invalid_operation_collections_are_rejected(operations):
    with pytest.raises(ConfigurationError):
        Adapter("custom", "library", operations)


def test_duplicate_operations_and_invalid_aliases_are_rejected():
    operation = Operation("run", lambda: None)
    with pytest.raises(ConfigurationError, match="unique"):
        Adapter("custom", "library", (operation, operation))
    with pytest.raises(ConfigurationError, match="sequence"):
        Adapter("custom", "library", (operation,), aliases="alias")
    with pytest.raises(ConfigurationError, match="iterable"):
        Adapter("custom", "library", (operation,), aliases=None)
    with pytest.raises(ConfigurationError, match="non-empty strings"):
        Adapter("custom", "library", (operation,), aliases=("",))
    with pytest.raises(ConfigurationError, match="description must be a string"):
        Adapter("custom", "library", (operation,), description=None)


def test_real_entry_point_loading_registers_a_factory_without_running_operations(monkeypatch):
    entry = install_entry(monkeypatch)
    set_entries(monkeypatch, entry)
    catalog = discover_adapters(strict=True)
    value = object()
    assert catalog.run("text", "identity", value) is value
    assert catalog.discovery_issues == ()
    assert discover_adapters() is not catalog


def test_discovery_is_empty_when_no_plugins_are_installed(monkeypatch):
    set_entries(monkeypatch)
    assert discover_adapters().adapters == ()


def test_discovery_keeps_working_plugins_and_preserves_broken_plugin_causes(monkeypatch):
    original = RuntimeError("incompatible plugin")

    def broken():
        raise original

    bad = install_entry(monkeypatch, name="broken", factory=broken, module="test_plugin_broken")
    good = install_entry(monkeypatch)
    set_entries(monkeypatch, bad, good)
    catalog = discover_adapters()
    assert catalog.get("text").name == "text"
    assert len(catalog.discovery_issues) == 1
    issue = catalog.discovery_issues[0]
    assert issue.name == "broken"
    assert issue.value == bad.value
    assert issue.error.__cause__ is original
    with pytest.raises(AdapterLoadError, match="incompatible plugin") as caught:
        discover_adapters(strict=True)
    assert caught.value.__cause__ is original


@pytest.mark.parametrize("factory", [lambda: None, lambda: make_adapter("different"), 42])
def test_invalid_entry_point_contracts_are_reported(monkeypatch, factory):
    entry = install_entry(monkeypatch, factory=factory)
    set_entries(monkeypatch, entry)
    catalog = discover_adapters()
    assert catalog.adapters == ()
    assert len(catalog.discovery_issues) == 1


def test_missing_plugin_module_is_reported_with_its_import_error(monkeypatch):
    entry = EntryPoint("missing", "pymplify_nonexistent_plugin:factory", "pymplify.adapters")
    set_entries(monkeypatch, entry)
    with pytest.raises(AdapterLoadError) as caught:
        discover_adapters(strict=True)
    assert isinstance(caught.value.__cause__, ModuleNotFoundError)


def test_discovery_conflicts_are_deterministic_and_never_overwrite(monkeypatch):
    first = install_entry(monkeypatch, module="test_plugin_alpha")
    second = install_entry(monkeypatch, module="test_plugin_zeta")
    set_entries(monkeypatch, second, first)
    catalog = discover_adapters()
    assert len(catalog.adapters) == 1
    assert catalog.discovery_issues[0].value == second.value
    assert "already registered" in str(catalog.discovery_issues[0].error)


def test_discovery_does_not_swallow_interruptions(monkeypatch):
    def interrupted():
        raise KeyboardInterrupt

    entry = install_entry(monkeypatch, factory=interrupted)
    set_entries(monkeypatch, entry)
    with pytest.raises(KeyboardInterrupt):
        discover_adapters()
