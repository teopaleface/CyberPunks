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


def test_whatsapp_handshake_uses_native_verification_not_app_bearer(monkeypatch, tmp_path):
    monkeypatch.setenv("DAYBREAK_CHANNELS_RUNTIME", str(tmp_path / "channels"))
    monkeypatch.setenv("DAYBREAK_INTERNAL_TOKEN", "runtime-test-token")
    monkeypatch.setenv("DAYBREAK_OPERATIONS_OUTPUTS", str(tmp_path / "data"))
    monkeypatch.setenv("DAYBREAK_WHATSAPP_ENABLED", "1")
    monkeypatch.setenv("DAYBREAK_META_VERIFY_TOKEN", "synthetic-verify-token")
    client = TestClient(create_app())
    response = client.get("/api/conversation/whatsapp/webhook", params={
        "hub.mode": "subscribe", "hub.verify_token": "synthetic-verify-token", "hub.challenge": "12345",
    })
    assert response.status_code == 200
    assert response.text == "12345"
    assert client.get("/api/conversation/whatsapp/webhook", params={"hub.verify_token": "wrong"}).status_code == 403
    assert client.get("/api/conversation/chat").status_code == 401


def test_whatsapp_native_signature_is_still_required(monkeypatch, tmp_path):
    import hashlib
    import hmac

    monkeypatch.setenv("DAYBREAK_INTERNAL_TOKEN", "runtime-test-token")
    monkeypatch.setenv("DAYBREAK_OPERATIONS_OUTPUTS", str(tmp_path / "data"))
    monkeypatch.setenv("DAYBREAK_CHANNELS_RUNTIME", str(tmp_path / "channels"))
    monkeypatch.setenv("DAYBREAK_WHATSAPP_ENABLED", "1")
    monkeypatch.setenv("DAYBREAK_META_APP_SECRET", "synthetic-meta-signing-secret")
    client = TestClient(create_app())
    body = b'{"object":"whatsapp_business_account","entry":[]}'
    assert client.post("/api/conversation/whatsapp/webhook", content=body).status_code == 401
    signature = "sha256=" + hmac.new(b"synthetic-meta-signing-secret", body, hashlib.sha256).hexdigest()
    response = client.post("/api/conversation/whatsapp/webhook", content=body, headers={"x-hub-signature-256": signature})
    assert response.status_code == 200
