import numpy as np
import pytest
from pymplify_analysis import analyze_code, analyze_file
from pymplify_core import ConfigurationError


@pytest.mark.parametrize(
    ("import_line", "constructor", "rule"),
    [
        (
            "from sklearn.feature_extraction.text import TfidfVectorizer as TF",
            "TF",
            "text-fit-transform",
        ),
        (
            "import sklearn.feature_extraction.text as text",
            "text.TfidfVectorizer",
            "text-fit-transform",
        ),
        (
            "import sklearn.preprocessing",
            "sklearn.preprocessing.StandardScaler",
            "tabular-fit-transform",
        ),
        (
            "from sklearn.preprocessing import StandardScaler",
            "StandardScaler",
            "tabular-fit-transform",
        ),
    ],
)
def test_supported_aliases_produce_evidence_and_unverified_previews(import_line, constructor, rule):
    source = f"{import_line}\nmodel = {constructor}()\noutput = model.fit_transform(data)\n"
    report = analyze_code(source, filename="example.py")
    assert len(report.suggestions) == 1
    item = report.suggestions[0]
    assert item.rule == rule
    assert item.locations[0].filename == "example.py"
    assert item.locations[0].line == 2
    assert item.locations[1].line == 3
    assert "model =" in item.original
    assert item.requirements and item.caveats and item.validation_steps
    assert not item.validated
    assert "output = _pymplify_result." in item.replacement


@pytest.mark.parametrize("kind", ["text", "tabular"])
def test_generated_preview_preserves_native_results_fitted_models_and_options(kind):
    if kind == "text":
        source = (
            "from sklearn.feature_extraction.text import TfidfVectorizer as Backend\n"
            "model = Backend(ngram_range=(1, 2), max_features=5)\n"
            "output = model.fit_transform(data)\n"
        )
        data, queries = ["small language model", "simple machine learning"], ["small model"]
    else:
        source = (
            "from sklearn.preprocessing import StandardScaler as Backend\n"
            "model = Backend(with_mean=False)\n"
            "output = model.fit_transform(data)\n"
        )
        data, queries = [[1.0, 2.0], [3.0, 4.0]], [[5.0, 6.0]]
    candidate = analyze_code(source).suggestions[0].replacement
    original_env, candidate_env = {"data": data}, {"data": data}
    # Execute only these trusted test fixtures; the analyzer itself never executes source.
    exec(source, original_env)
    exec(candidate, candidate_env)
    assert type(original_env["model"]) is type(candidate_env["model"])
    assert original_env["model"].get_params() == candidate_env["model"].get_params()
    for left, right in [
        (original_env["output"], candidate_env["output"]),
        (original_env["model"].transform(queries), candidate_env["model"].transform(queries)),
    ]:
        if hasattr(left, "toarray"):
            left, right = left.toarray(), right.toarray()
        np.testing.assert_allclose(left, right)


def test_analysis_does_not_execute_imports_calls_or_top_level_exceptions(tmp_path):
    marker = tmp_path / "executed"
    source = (
        f"import definitely_missing_library\nopen({str(marker)!r}, 'w').write('bad')\n"
        "raise RuntimeError\n"
    )
    report = analyze_code(source)
    assert report.imports == ("definitely_missing_library",)
    assert not marker.exists()


@pytest.mark.parametrize(
    "body",
    [
        "Backend = replacement\nmodel = Backend()\noutput = model.fit_transform(data)",
        "def workflow(Backend):\n model = Backend()\n output = model.fit_transform(data)",
        (
            "def workflow():\n model = Backend()\n output = model.fit_transform(data)\n"
            " Backend = replacement"
        ),
        "for Backend in values:\n model = Backend()\n output = model.fit_transform(data)",
        "with manager() as Backend:\n model = Backend()\n output = model.fit_transform(data)",
    ],
)
def test_obvious_shadowing_does_not_recommend_a_known_adapter(body):
    source = "from sklearn.preprocessing import StandardScaler as Backend\n" + body
    assert not analyze_code(source).suggestions


def test_module_shadowing_and_unimported_qualified_names_are_not_assumed_to_be_upstream():
    workflow = "model = sklearn.preprocessing.StandardScaler()\noutput = model.fit_transform(data)"
    assert not analyze_code(workflow).suggestions
    assert not analyze_code("import sklearn\nsklearn = replacement\n" + workflow).suggestions


def test_wildcard_import_invalidates_previously_known_bindings():
    source = (
        "from sklearn.preprocessing import StandardScaler\n"
        "from unknown_library import *\n"
        "model = StandardScaler()\noutput = model.fit_transform(data)"
    )
    assert not analyze_code(source).suggestions


@pytest.mark.parametrize(
    "body",
    [
        "model = Backend(**options)\noutput = model.fit_transform(data)",
        "model = Backend(1)\noutput = model.fit_transform(data)",
        "model = Backend()\noutput = model.fit_transform(data, labels)",
        "model = Backend()\noutput = model.fit_transform(X=data)",
        "model = Backend()\noutput = model.fit_transform(*data)",
        "model = Backend()\nprint('intervening statement')\noutput = model.fit_transform(data)",
        "model = Backend()\noutput = other.fit_transform(data)",
        "Backend = Backend()\noutput = Backend.fit_transform(data)",
        "model = Backend()\nmodel.fit_transform(data)",
    ],
)
def test_unsupported_call_shapes_are_not_presented_as_adapter_matches(body):
    source = "from sklearn.preprocessing import StandardScaler as Backend\n" + body
    assert not any(item.rule.endswith("fit-transform") for item in analyze_code(source).suggestions)


def test_nested_function_imports_work_and_temporary_names_do_not_collide():
    report = analyze_code("""
def workflow(data):
    from sklearn.preprocessing import StandardScaler as Backend
    _pymplify_result = 'already used'
    model = Backend()
    output = model.fit_transform(data)
    return _pymplify_result, output
""")
    assert len(report.suggestions) == 1
    assert "_pymplify_result_ = scale(data)" in report.suggestions[0].replacement


def test_repeated_call_pairs_are_located_without_claiming_semantic_equivalence():
    source = """from library import prepare, predict
x = prepare(first)
y = predict(x)
print('separate spans')
x = prepare(second)
y = predict(x)
"""
    report = analyze_code(source)
    item = next(item for item in report.suggestions if item.rule == "repeated-call-pair")
    assert [location.line for location in item.locations] == [2, 5]
    assert item.replacement is None
    assert "library.prepare" in item.title
    assert not analyze_code(source, min_repetitions=3).suggestions


def test_overlapping_pairs_and_control_flow_are_not_counted_as_independent_repetitions():
    assert not analyze_code("model.run()\nmodel.run()\nmodel.run()").suggestions
    assert len(analyze_code("model.run()\nmodel.run()\nmodel.run()\nmodel.run()").suggestions) == 1
    assert not analyze_code("if flag:\n model.prepare()\nelse:\n model.run()").suggestions


def test_source_files_respect_declared_encoding_and_limits(tmp_path):
    path = tmp_path / "encoded.py"
    path.write_bytes("# coding: latin-1\nvalue = 'caf\xe9'\n".encode("latin-1"))
    assert analyze_file(path).filename == str(path)
    with pytest.raises(ConfigurationError, match="exceeds"):
        analyze_file(path, max_file_bytes=1)
    with pytest.raises(ConfigurationError, match="Cannot read"):
        analyze_file(tmp_path / "missing.py")


@pytest.mark.parametrize("source", ["def invalid(:", "x = '\\x00'".replace("\\x00", "\x00"), None])
def test_invalid_source_has_actionable_parse_errors(source):
    with pytest.raises(ConfigurationError):
        analyze_code(source, filename="broken.py")


@pytest.mark.parametrize("count", [1, True, 0, "2"])
def test_repetition_threshold_is_validated(count):
    with pytest.raises(ConfigurationError, match="min_repetitions"):
        analyze_code("", min_repetitions=count)
