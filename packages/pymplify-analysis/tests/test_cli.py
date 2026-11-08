import json
import subprocess
import sys

import pytest
from pymplify_analysis.cli import main

SOURCE = """from sklearn.preprocessing import StandardScaler
model = StandardScaler()
output = model.fit_transform(data)
"""


def test_code_cli_json_is_structured_and_does_not_execute_input(tmp_path, capsys):
    path = tmp_path / "workflow.py"
    path.write_text(SOURCE + "raise RuntimeError('do not execute')\n", encoding="utf-8")
    assert main(["code", str(path), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["suggestions"][0]["validated"] is False
    assert payload["suggestions"][0]["locations"][0]["line"] == 2


def test_text_reports_include_evidence_caveats_and_validation_steps(tmp_path, capsys):
    path = tmp_path / "workflow.py"
    path.write_text(SOURCE, encoding="utf-8")
    main(["code", str(path)])
    output = capsys.readouterr().out
    assert "unverified" in output and "Requires:" in output
    assert "Review:" in output and "Validate:" in output


def test_library_cli_json_and_text(tmp_path, capsys):
    (tmp_path / "api.py").write_text("def predict(value): return value", encoding="utf-8")
    main(["library", str(tmp_path), "--json"])
    assert json.loads(capsys.readouterr().out)["functions"][0]["name"] == "predict"
    main(["library", str(tmp_path)])
    output = capsys.readouterr().out
    assert "api.predict(value)" in output and "Truncated: False" in output


def test_cli_reports_issues_and_configuration_errors(tmp_path, capsys):
    main(["library", str(tmp_path)])
    assert "Issue:" in capsys.readouterr().out
    with pytest.raises(SystemExit) as caught:
        main(["code", str(tmp_path / "missing.py")])
    assert caught.value.code == 2
    assert "Cannot read" in capsys.readouterr().err


def test_installed_module_cli_works_in_isolated_python(tmp_path):
    path = tmp_path / "workflow.py"
    path.write_text(SOURCE, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-I", "-m", "pymplify_analysis", "code", str(path), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["suggestions"][0]["rule"] == "tabular-fit-transform"
