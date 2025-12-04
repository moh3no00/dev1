import json
from pathlib import Path

import backend.analyzer as analyzer


def test_run_php_analysis_collects_tool_output(monkeypatch, tmp_path):
    def fake_run(command, capture_output, text, check):
        class Result:
            pass

        result = Result()
        if command[0] == "phpstan":
            result.returncode = 1
            result.stdout = "Line 3: Parse error"
            result.stderr = ""
        else:
            result.returncode = 1
            payload = {
                "files": {
                    "sample.php": {
                        "messages": [
                            {"line": 5, "message": "Missing function doc comment"}
                        ]
                    }
                }
            }
            result.stdout = json.dumps(payload)
            result.stderr = ""
        return result

    monkeypatch.setattr(analyzer.subprocess, "run", fake_run)

    code = "<?php echo 'hi'"  # missing semicolon to trigger error
    report = analyzer.run_php_analysis(code, "sample.php", workspace=tmp_path)

    assert Path(report["file"]).name == "sample.php"
    errors = report["errors"]
    assert any(error["tool"] == "phpstan" for error in errors)
    assert any("Missing function doc comment" in error["message"] for error in errors)


def test_sanitize_rejects_outside_workspace(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    try:
        analyzer.sanitize_relative_path("../evil.php", workspace)
    except analyzer.AnalysisError as exc:
        assert "outside" in str(exc)
    else:
        raise AssertionError("Expected AnalysisError for escaping workspace")
