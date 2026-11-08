"""Synthetic ingress security cases; no live runtime requests."""

import json

import httpx
from fastapi.testclient import TestClient

from cyberpunks.operations.bindings import DEMO_ORGANIZATION
from cyberpunks.workspace_ingress import create_app


def test_restricted_proxy(monkeypatch):
    monkeypatch.setenv("DAYBREAK_INTERNAL_TOKEN", "synthetic-token")
    calls = []

    def upstream(request):
        calls.append(request)
        return httpx.Response(200, json={"ok": True})

    client = TestClient(create_app(transport=httpx.MockTransport(upstream)))
    headers = {
        "authorization": "Bearer synthetic-token",
        "x-daybreak-actor": json.dumps(
            {
                "user_id": "synthetic",
                "role": "dispatcher",
                "organization_id": DEMO_ORGANIZATION,
                "permissions": ["view_console"],
            }
        ),
    }
    assert client.get("/healthz").json() == {"status": "ok"}
    assert client.get("/api/plan").status_code == 401
    for path in ["/docs", "/openapi.json", "/webhook", "/api/operations/bindings", "/api/conversation/tasks"]:
        assert client.get(path, headers=headers).status_code == 404
    assert client.post("/api/plan", headers=headers).status_code == 404
    assert client.get("/api/plan?scenario=other", headers=headers).status_code == 403
    assert client.post("/api/conversation/tasks", headers=headers, content=b"x" * 65001).status_code == 413
    assert not calls
    for method, path in [
        ("GET", "/api/plan"),
        ("GET", "/api/conversation/tasks/task_1"),
        ("POST", "/api/conversation/tasks"),
        ("POST", "/api/conversation/tasks/task_1/resume"),
        ("POST", "/api/conversation/tasks/task_1/recommendations/A-20250708-PT-1182/prepare"),
    ]:
        assert client.request(method, path, headers={**headers, "cookie": "secret"}).status_code == 200
        assert calls[-1].url.host == "127.0.0.1"
        assert calls[-1].url.port == 8720
        assert calls[-1].url.path == path
        assert "cookie" not in calls[-1].headers
    for role, org in [("customer", DEMO_ORGANIZATION), ("dispatcher", "other")]:
        actor = {"user_id": "synthetic", "role": role, "organization_id": org}
        assert client.get("/api/plan", headers={**headers, "x-daybreak-actor": json.dumps(actor)}).status_code == 403


def test_fail_closed_and_redirect(monkeypatch):
    client = TestClient(
        create_app(
            transport=httpx.MockTransport(
                lambda r: httpx.Response(302, headers={"location": "https://example.com"}, text="secret")
            )
        )
    )
    monkeypatch.delenv("DAYBREAK_INTERNAL_TOKEN", raising=False)
    assert client.get("/api/plan").status_code == 503
    monkeypatch.setenv("DAYBREAK_INTERNAL_TOKEN", "synthetic-token")
    headers = {
        "authorization": "Bearer synthetic-token",
        "x-daybreak-actor": json.dumps(
            {
                "user_id": "synthetic",
                "role": "dispatcher",
                "organization_id": DEMO_ORGANIZATION,
                "permissions": ["view_console"],
            }
        ),
    }
    response = client.get("/api/plan", headers=headers)
    assert response.status_code == 502
    assert "secret" not in response.text
    assert client.get("/api/plan", headers={**headers, "x-daybreak-actor": "{}"}).status_code == 401
