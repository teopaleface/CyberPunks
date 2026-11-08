import hashlib
import hmac

from fastapi.testclient import TestClient

from cyberpunks.webhook_runtime import create_app


def test_public_ingress_exposes_only_native_meta_webhook(monkeypatch, tmp_path):
    monkeypatch.setenv("DAYBREAK_CHANNELS_RUNTIME", str(tmp_path))
    monkeypatch.setenv("DAYBREAK_WHATSAPP_ENABLED", "1")
    monkeypatch.setenv("DAYBREAK_META_VERIFY_TOKEN", "synthetic-verify-token")
    client = TestClient(create_app())
    for path in ("/", "/docs", "/openapi.json", "/api/plan", "/api/operations/context", "/api/conversation/chat"):
        assert client.get(path).status_code == 404
        assert client.post(path, json={}).status_code == 404
    query = {"hub.mode": "subscribe", "hub.verify_token": "synthetic-verify-token", "hub.challenge": "12345"}
    assert client.get("/api/conversation/whatsapp/webhook", params=query).text == "12345"
    query["hub.verify_token"] = "wrong"
    assert client.get("/api/conversation/whatsapp/webhook", params=query).status_code == 403


def test_public_ingress_requires_signature_before_accepting_event(monkeypatch, tmp_path):
    monkeypatch.setenv("DAYBREAK_CHANNELS_RUNTIME", str(tmp_path))
    monkeypatch.setenv("DAYBREAK_WHATSAPP_ENABLED", "1")
    monkeypatch.setenv("DAYBREAK_META_APP_SECRET", "synthetic-app-secret")
    client = TestClient(create_app())
    body = b'{"object":"whatsapp_business_account","entry":[]}'
    path = "/api/conversation/whatsapp/webhook"
    assert client.post(path, content=body).status_code == 401
    signature = "sha256=" + hmac.new(b"synthetic-app-secret", body, hashlib.sha256).hexdigest()
    assert client.post(path, content=body, headers={"x-hub-signature-256": signature}).status_code == 200
