"""Long work must not occupy the voice request or block the next question."""

import asyncio
import threading
import time

from fastapi.testclient import TestClient

from cyberpunks.channels.voice_jobs import VoiceJobs
from cyberpunks.channels.whatsapp_calls import create_app, is_dispatch_request

from .test_whatsapp_calls import demo_call  # noqa: F401


def test_real_call_dispatch_request_is_explicitly_routed():
    assert is_dispatch_request("Păi, vreau să fac-- vreau să faci tu asta pentru mine, rezolvă toate cazurile.")
    assert is_dispatch_request("Pot să le rezolv pe între mine?")
    for text in ("Nu rezolva toate cazurile", 'A spus "rezolvă toate cazurile"', "Cum rezolv toate cazurile?"):
        assert not is_dispatch_request(text)


def test_pdf_is_queued_immediately_and_the_next_question_still_works(demo_call, env, monkeypatch):  # noqa: F811
    from cyberpunks.channels import voice_briefs

    monkeypatch.setattr(voice_briefs, "answer_demo", demo_call["real_brief"])
    started, finish = threading.Event(), threading.Event()
    sent = []

    async def sender(operations, actor, **kwargs):
        assert kwargs["authorize_actor"]() == actor
        started.set()
        while not finish.is_set():
            await asyncio.sleep(0.01)
        sent.append(actor.role)
        return {"status": "delivered", "reply": "Raportul PDF a fost livrat pe WhatsApp."}

    demo_call["entry"]["allow_voice_reports"] = True
    store = VoiceJobs(env["tmp"] / "synthetic-voice.sqlite3")
    app = create_app(
        service=env["conversation"],
        bindings=demo_call["bindings"],
        config_loader=lambda: demo_call["config"],
        report_sender=sender,
        background_jobs=True,
        job_store=store,
    )
    body = {
        "caller_id": "+40700000000",
        "conversation_id": "synthetic-background",
        "message": "Trimite-mi raportul pe WhatsApp.",
    }
    with TestClient(app) as client:
        begin = time.monotonic()
        response = client.post("/api/voice/turn", headers=demo_call["headers"], json=body)
        assert response.status_code == 200 and "Pregătesc raportul" in response.json()["reply"]
        assert time.monotonic() - begin < 2 and not sent
        assert started.wait(2)
        second = client.post(
            "/api/voice/turn", headers=demo_call["headers"], json={**body, "message": "Ce am de făcut astăzi?"}
        )
        assert second.status_code == 200 and "aprobat" in second.json()["reply"]
        finish.set()
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline and not sent:
            time.sleep(0.01)
        assert sent == ["technician"]
        while (
            time.monotonic() < deadline
            and store.latest(env["actors"]["technician"], body["conversation_id"])["status"] != "done"
        ):
            time.sleep(0.01)
        duplicate = client.post("/api/voice/turn", headers=demo_call["headers"], json=body)
        assert "livrat" in duplicate.json()["reply"] and sent == ["technician"]


def test_dispatch_job_applies_real_decisions_and_approves_resulting_plan(demo_call, env, monkeypatch):  # noqa: F811
    from cyberpunks.channels import voice_dispatch

    from .test_voice_dispatch import SyntheticProvider

    actual = voice_dispatch.run_dispatch

    async def grounded(operations, actor, **kwargs):
        return await actual(operations, actor, **kwargs, provider=SyntheticProvider())

    monkeypatch.setattr(voice_dispatch, "run_dispatch", grounded)
    demo_call["entry"]["allow_queue_actions"] = True
    store = VoiceJobs(env["tmp"] / "synthetic-dispatch-voice.sqlite3")
    app = create_app(
        service=env["conversation"],
        bindings=demo_call["bindings"],
        config_loader=lambda: demo_call["config"],
        background_jobs=True,
        job_store=store,
    )
    client = TestClient(app)
    payload = {
        "caller_id": "+40700000000",
        "conversation_id": "synthetic-dispatch-live-flow",
        "message": "Sunt dispecer. Rezolvă toate cazurile pentru mine.",
    }
    response = client.post("/api/voice/turn", headers=demo_call["headers"], json=payload)
    assert response.status_code == 200 and "Analizez coada" in response.json()["reply"]
    finished = asyncio.run(store.drain_one(app.state.voice_job_handler))
    assert finished["status"] == "done", finished
    result = finished["result"]
    assert result["applied"] > 0 and result["plan_approval"]["status"] == "succeeded"
    actor = env["actors"]["dispatcher"].model_copy(
        update={"permissions": demo_call["entry"]["actors"]["dispatcher"]["permissions"]}
    )
    assert env["operations"].context(actor)["plan"]["approved"] is True
    duplicate = client.post("/api/voice/turn", headers=demo_call["headers"], json=payload)
    assert "Am aplicat" in duplicate.json()["reply"]
    assert asyncio.run(store.drain_one(app.state.voice_job_handler)) is None
