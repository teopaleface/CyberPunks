"""Caller isolation and confirmation boundaries on a fresh complete operational data copy."""

import json

import pytest
from fastapi.testclient import TestClient

from cyberpunks.channels.whatsapp_calls import call_agent_config, create_app


@pytest.fixture
def call_api(env):
    class VerifiedBinding:
        def resolve(self, destination, sender):
            assert destination == "synthetic-phone" and sender == "40700000000"
            return env["actors"]["technician"]

    config = {"tool_token": "synthetic-private-token", "phone_number_id": "synthetic-phone", "allowed_callers": ["40700000000"]}
    client = TestClient(create_app(service=env["conversation"], bindings=VerifiedBinding(), config_loader=lambda: config))
    return client, {"Authorization": "Bearer synthetic-private-token"}


def payload(**changes):
    return {"message": "Salut! Ce vezi?", "caller_id": "+40700000000", "conversation_id": "synthetic-call", **changes}


def test_call_tool_authenticates_before_parsing_or_loading_private_context(call_api, env):
    client, _ = call_api
    response = client.post("/api/voice/turn", content="not-json")
    assert response.status_code == 401
    assert not env["provider"].prompts


def test_call_tool_rejects_foreign_caller_and_body_selected_role(call_api, env):
    client, headers = call_api
    assert client.post("/api/voice/turn", headers=headers, json=payload(caller_id="40711111111")).status_code == 403
    assert client.post("/api/voice/turn", headers=headers, json={**payload(), "role": "dispatcher"}).status_code == 422
    assert not env["provider"].prompts


def test_real_actor_scope_and_history_are_server_selected_without_confirmation(call_api, env):
    client, headers = call_api
    first = client.post("/api/voice/turn", headers=headers, json=payload())
    assert first.status_code == 200 and set(first.json()) == {"reply"}
    second = client.post("/api/voice/turn", headers=headers, json=payload(message="De ce?"))
    assert second.status_code == 200
    data = json.loads(env["provider"].prompts[-1].split("INPUT JSON:\n")[1])
    assert data["role"] == "technician"
    assert data["history"] == [
        {"role": "user", "content": payload()["message"]},
        {"role": "assistant", "content": first.json()["reply"]},
    ]
    assert client.post("/api/operations/confirm", headers=headers, json={}).status_code == 404


def test_changed_call_binding_cannot_reuse_the_old_context(call_api, env):
    client, headers = call_api
    assert client.post("/api/voice/turn", headers=headers, json=payload()).status_code == 200
    env["actors"]["technician"] = env["actors"]["technician"].model_copy(update={"user_id": "different-synthetic-user"})
    response = client.post("/api/voice/turn", headers=headers, json=payload(message="Continue"))
    assert response.status_code == 403 and response.json()["error"] == "call_identity_changed"


def test_call_provider_failure_keeps_credentials_out_of_response(call_api, env):
    client, headers = call_api
    env["provider"].error = RuntimeError("synthetic-secret-never-in-response")
    response = client.post("/api/voice/turn", headers=headers, json=payload())
    assert response.status_code == 503 and "synthetic-secret" not in response.text


def test_call_agent_identity_fields_are_injected_by_provider_and_never_chosen_by_llm():
    config = call_agent_config("syntheticvoice123", "https://synthetic.trycloudflare.com", "synthetic-secret-id")
    assert config["platform_settings"]["auth"]["enable_auth"] is True
    tools = config["conversation_config"]["agent"]["prompt"]["tools"]
    assert len(tools) == 1 and tools[0]["type"] == "webhook"
    schema = tools[0]["api_schema"]
    assert schema["request_headers"] == {"Authorization": {"secret_id": "synthetic-secret-id"}}
    assert schema["request_body_schema"]["properties"]["caller_id"] == {
        "type": "string", "dynamic_variable": "system__caller_id",
    }
    assert not tools[0]["follow_redirects"]
