"""Exact role-switch utterances captured from the reported physical call."""

import pytest
from fastapi.testclient import TestClient

from cyberpunks.channels.whatsapp_calls import _role_declaration, create_app

from .test_whatsapp_calls import demo_call, demo_turn  # noqa: F401


@pytest.mark.parametrize(
    "message",
    [
        "Ă, sunt dispecer. Câte tichete am și câte au risc de siguranță?",
        "Dispecer PPC.",
        "Aleg rolul de dispecer PPC. Câte tichete am și câte risc de siguranță?",
    ],
)
def test_actual_dispatcher_retries_select_the_preapproved_role(message):
    role, _, ambiguous = _role_declaration(message)
    assert role == "dispatcher" and not ambiguous


def test_all_four_requests_in_one_call_with_real_scoped_answers(demo_call, env, monkeypatch):  # noqa: F811
    from cyberpunks.channels import voice_briefs

    monkeypatch.setattr(voice_briefs, "answer_demo", demo_call["real_brief"])
    reports = []

    async def report(operations, actor, **kwargs):
        assert kwargs["authorize_actor"]() == actor
        reports.append((actor.role, kwargs["event_key"]))
        return {"reply": "Raportul PDF a fost livrat pe WhatsApp."}

    demo_call["entry"]["allow_voice_reports"] = True
    demo_call["client"] = TestClient(
        create_app(
            service=env["conversation"],
            bindings=demo_call["bindings"],
            config_loader=lambda: demo_call["config"],
            report_sender=report,
        )
    )
    first = demo_turn(demo_call, "Sunt client. Raportez că mi-a căzut un stâlp de curent.")
    assert first.status_code == 200 and "Demo client." in first.json()["reply"]
    second = demo_turn(demo_call, "Ă, sunt dispecer. Câte tichete am și câte au risc de siguranță?")
    assert second.status_code == 200 and "tichete" in second.json()["reply"]
    assert "Ce rol alegi" not in second.json()["reply"]
    assert second.json()["reply"].startswith("Demo dispecer.")
    for correction in ("Dispecer PPC.", "Aleg rolul de dispecer PPC. Câte tichete am și câte risc de siguranță?"):
        retried = demo_turn(demo_call, correction)
        assert retried.status_code == 200 and "tichete" in retried.json()["reply"]
        assert "Ce rol alegi" not in retried.json()["reply"]
    third = demo_turn(demo_call, "Ă, sunt tehnician PPC. Ce am de făcut astăzi? Trebuie echipament?")
    assert third.status_code == 200 and "Demo tehnician." in third.json()["reply"]
    fourth = demo_turn(demo_call, "Trimite-mi raportul pe WhatsApp.")
    assert fourth.status_code == 200 and "livrat" in fourth.json()["reply"]
    assert len(reports) == 1 and reports[0][0] == "technician"
    assert not env["provider"].prompts
