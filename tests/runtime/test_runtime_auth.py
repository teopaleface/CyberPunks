from fastapi.testclient import TestClient

from cyberpunks.runtime import create_app


def test_runtime_rejects_private_routes_without_internal_token(monkeypatch, tmp_path):
    monkeypatch.setenv("DAYBREAK_INTERNAL_TOKEN", "runtime-test-token")
    monkeypatch.setenv("DAYBREAK_OPERATIONS_OUTPUTS", str(tmp_path / "data"))
    client = TestClient(create_app())
    assert client.get("/healthz").json()["status"] == "ok"
    assert client.get("/api/plan").status_code == 401
    assert client.get("/api/operations/context").status_code == 401
    assert client.post("/api/conversation/chat", json={"message": "hello"}).status_code == 401


def test_runtime_never_treats_internal_token_as_a_user_identity(monkeypatch, tmp_path):
    monkeypatch.setenv("DAYBREAK_INTERNAL_TOKEN", "runtime-test-token")
    monkeypatch.setenv("DAYBREAK_OPERATIONS_OUTPUTS", str(tmp_path / "data"))
    client = TestClient(create_app())
    response = client.get("/api/operations/context", headers={"Authorization": "Bearer runtime-test-token"})
    assert response.status_code in (401, 403, 422)


def test_runtime_requires_explicit_private_configuration(monkeypatch):
    monkeypatch.delenv("DAYBREAK_INTERNAL_TOKEN", raising=False)
    client = TestClient(create_app())
    assert client.get("/api/plan", headers={"Authorization": "Bearer arbitrary"}).status_code == 503


def test_legacy_mutations_cannot_bypass_shared_proposals(monkeypatch, tmp_path):
    monkeypatch.setenv("DAYBREAK_INTERNAL_TOKEN", "runtime-test-token")
    monkeypatch.setenv("DAYBREAK_OPERATIONS_OUTPUTS", str(tmp_path / "data"))
    client = TestClient(create_app())
    headers = {"Authorization": "Bearer runtime-test-token"}
    for path in ("/api/run", "/api/plan/approve", "/api/review/A-20250708-other"):
        assert client.post(path, headers=headers, json={}).status_code == 409
