from fastapi.testclient import TestClient

from backend import main
from backend.model_client import PatchSuggestion


def test_fix_endpoint_returns_patch(monkeypatch):
    def fake_analysis(code, path):
        return {"file": path, "errors": [{"tool": "phpstan", "message": "Missing semicolon"}]}

    class StubClient:
        def request_patch(self, errors, code, path, context):
            assert "phpstan" in errors
            return PatchSuggestion(diff="---diff---", summary="fixed missing semicolon")

    monkeypatch.setattr(main.analyzer, "run_php_analysis", fake_analysis)
    monkeypatch.setattr(main, "model_client", StubClient())

    client = TestClient(main.app)
    response = client.post(
        "/fix",
        json={"code": "<?php echo 'hi'", "path": "src/app.php", "context": "fix echo"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["patch"] == "---diff---"
    assert body["explanation"] == "fixed missing semicolon"
    assert body["analysis"][0]["tool"] == "phpstan"


def test_fix_endpoint_rejects_bad_path(monkeypatch):
    def fake_analysis(code, path):
        raise main.analyzer.AnalysisError("Invalid path")

    monkeypatch.setattr(main.analyzer, "run_php_analysis", fake_analysis)

    client = TestClient(main.app)
    response = client.post(
        "/fix",
        json={"code": "<?php echo 'hi'", "path": "../escape.php", "context": "fix"},
    )

    assert response.status_code == 400
    assert "Invalid path" in response.json()["detail"]
