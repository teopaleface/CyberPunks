"""The setup boundary must preserve another callback and fail closed after uncertain writes."""

import importlib.util
import os
from pathlib import Path

import httpx
import pytest

pytestmark = pytest.mark.skipif(
    os.name == "nt",
    reason="WhatsApp private-file setup requires POSIX permissions; use WSL2 on Windows.",
)


@pytest.fixture
def setup_module(monkeypatch, tmp_path):
    path = Path(__file__).resolve().parents[2] / "scripts/daybreak_whatsapp_setup.py"
    spec = importlib.util.spec_from_file_location("daybreak_setup_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "CONFIG", tmp_path / "meta.env")
    monkeypatch.setattr(module, "RECORD", tmp_path / "verified.json")
    module.save(
        {
            "DAYBREAK_META_ACCESS_TOKEN": "synthetic-user-token",
            "DAYBREAK_META_APP_SECRET": "synthetic-app-secret",
            "DAYBREAK_META_PHONE_NUMBER_ID": module.PHONE_ID,
            "DAYBREAK_META_MESSAGING_ACCOUNT_ID": module.WABA_ID,
            "DAYBREAK_META_GRAPH_VERSION": "v25.0",
        }
    )
    return module


def mock_graph(monkeypatch, module, handler):
    real_client = httpx.Client
    monkeypatch.setattr(module.httpx, "Client", lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw))


@pytest.mark.parametrize("valid,app_matches", [(False, True), (True, False)])
def test_refresh_rejects_expired_or_foreign_tokens_without_writing(setup_module, monkeypatch, valid, app_matches):
    module = setup_module
    before = module.CONFIG.read_bytes()

    def handler(request):
        assert request.method == "GET"
        return httpx.Response(200, json={"data": {
            "is_valid": valid, "app_id": module.APP_ID if app_matches else "another-app", "expires_at": 0,
        }})

    mock_graph(monkeypatch, module, handler)
    with pytest.raises(SystemExit, match="existing token was preserved"):
        module.refresh_token("synthetic-new-token-for-this-test")
    assert module.CONFIG.read_bytes() == before


def test_refresh_validates_number_and_changes_only_private_token(setup_module, monkeypatch):
    module = setup_module
    before = module.private_env(module.CONFIG)
    calls = []

    def handler(request):
        calls.append(request)
        assert request.method == "GET"
        if request.url.path.endswith("debug_token"):
            return httpx.Response(200, json={"data": {
                "is_valid": True, "app_id": module.APP_ID, "expires_at": 0,
                "scopes": ["whatsapp_business_messaging"],
            }})
        return httpx.Response(200, json={"id": module.PHONE_ID})

    mock_graph(monkeypatch, module, handler)
    token = "synthetic-new-token-for-this-test"
    module.refresh_token(token)
    assert module.private_env(module.CONFIG) == {**before, "DAYBREAK_META_ACCESS_TOKEN": token}
    assert module.CONFIG.stat().st_mode & 0o077 == 0
    assert len(calls) == 2


def test_an_existing_unrelated_callback_is_preserved(setup_module, monkeypatch):
    module = setup_module
    baseline = module.CONFIG.read_bytes()
    methods = []

    def handler(request):
        methods.append(request.method)
        if request.url.path.endswith("/subscriptions"):
            return httpx.Response(
                200,
                json={
                    "data": [
                        {"object": "whatsapp_business_account", "callback_url": "https://existing.example/webhook"}
                    ]
                },
            )
        return httpx.Response(200, json={"id": module.APP_ID, "name": "Daybreak CyberPunks"})

    mock_graph(monkeypatch, module, handler)
    with pytest.raises(SystemExit, match="another callback"):
        module.connect("https://synthetic-test.trycloudflare.com" + module.WEBHOOK_PATH)
    assert methods == ["GET", "GET"]
    assert module.CONFIG.read_bytes() == baseline
    assert not module.RECORD.exists()


def test_sending_stays_disabled_when_persisted_fields_are_missing(setup_module, monkeypatch):
    module = setup_module
    callback = "https://synthetic-test.trycloudflare.com" + module.WEBHOOK_PATH
    reads = 0

    def handler(request):
        nonlocal reads
        if request.method == "POST":
            return httpx.Response(200, json={"success": True})
        if request.url.path.endswith("/subscriptions"):
            reads += 1
            return httpx.Response(
                200,
                json={
                    "data": []
                    if reads == 1
                    else [
                        {"object": "whatsapp_business_account", "callback_url": callback, "active": True, "fields": []}
                    ]
                },
            )
        if request.url.path.endswith("/subscribed_apps"):
            return httpx.Response(200, json={"data": [{"whatsapp_business_api_data": {"id": module.APP_ID}}]})
        return httpx.Response(200, json={"id": module.APP_ID, "name": "Daybreak CyberPunks"})

    mock_graph(monkeypatch, module, handler)
    with pytest.raises(SystemExit, match="verification is incomplete"):
        module.connect(callback)
    config = module.private_env(module.CONFIG)
    assert config["DAYBREAK_WHATSAPP_SEND_ENABLED"] == "0"
    assert not module.RECORD.exists()


def test_public_workspace_url_is_rejected_before_any_configuration_write(setup_module):
    module = setup_module
    baseline = module.CONFIG.read_bytes()
    with pytest.raises(SystemExit, match="exact Meta webhook path"):
        module.connect("https://synthetic-test.trycloudflare.com/workspace")
    assert module.CONFIG.read_bytes() == baseline
