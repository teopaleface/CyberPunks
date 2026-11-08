"""Explicit private-demo actions use server roles, never declarations as authority."""

import pytest

from cyberpunks.channels.models import ChannelError
from cyberpunks.channels.whatsapp_calls import clarified_incident, create_app, is_report_request

from .test_whatsapp_calls import demo_call, demo_turn  # noqa: F401


@pytest.mark.parametrize("message", ["Trimite-mi raportul pe WhatsApp", "Îmi trimiți PDF-ul?", "Vreau raportul"])
def test_explicit_report_request(message):
    assert is_report_request(message)


@pytest.mark.parametrize("message", ['A spus "trimite raportul"', "Nu trimite raportul", "Dacă vreau raportul?", "da"])
def test_non_requests_cannot_send(message):
    assert not is_report_request(message)


def test_incident_clarification_requires_the_server_question_and_specific_answer():
    history = [{"role": "assistant", "content": "Te referi la un stâlp căzut sau la o întrerupere de curent?"}]
    assert clarified_incident("Un stâlp căzut.", history) == "Raportez că a căzut un stâlp de curent."
    assert clarified_incident("Întrerupere de curent", history) == "Am rămas fără curent."
    for message in ("da", "Nu, stâlpul", '"stâlpul"', "Poate un stâlp"):
        assert clarified_incident(message, history) == message
    assert clarified_incident("Un stâlp căzut.", []) == "Un stâlp căzut."


def test_report_uses_selected_verified_actor_and_rechecks_revocation(demo_call, env):  # noqa: F811
    calls = []

    async def send(operations, actor, **kwargs):
        assert kwargs["authorize_actor"]() == actor
        calls.append(actor.role)
        demo_call["bindings"].revoked = True
        with pytest.raises(ChannelError):
            kwargs["authorize_actor"]()
        return {"reply": "Raportul nu a fost trimis deoarece accesul a fost revocat."}

    demo_call["entry"]["allow_voice_reports"] = True
    from fastapi.testclient import TestClient

    demo_call["client"] = TestClient(
        create_app(
            service=env["conversation"],
            bindings=demo_call["bindings"],
            config_loader=lambda: demo_call["config"],
            report_sender=send,
        )
    )
    response = demo_turn(demo_call, "Sunt dispecer. Trimite-mi raportul pe WhatsApp")
    assert response.status_code == 200
    assert calls == ["dispatcher"]
    assert "nu a fost trimis" in response.json()["reply"]


def test_incident_execution_flag_is_private_server_configuration(demo_call, env, monkeypatch):  # noqa: F811
    from cyberpunks.channels import voice_briefs

    flags = []

    def brief(operations, actor, message, **kwargs):
        flags.append((actor.role, kwargs.get("execute_incident", False)))
        return {"reply": "Rezultat verificat."}

    monkeypatch.setattr(voice_briefs, "answer_demo", brief)
    assert demo_turn(demo_call, "Sunt client. Mi-a picat curentul").status_code == 200
    demo_call["entry"]["allow_incident_actions"] = True
    assert (
        demo_turn(demo_call, "Sunt client. Mi-a picat curentul", conversation_id="synthetic-enabled").status_code == 200
    )
    assert flags == [("customer", False), ("customer", True)]
