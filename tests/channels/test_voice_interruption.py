"""Physical-call failures: a cancelled slow turn poisoned the next voice call."""

import asyncio

import httpx
from fastapi.testclient import TestClient

from cyberpunks.channels.whatsapp_calls import _role_declaration, create_app

from .test_whatsapp_calls import demo_call  # noqa: F401


def test_actual_role_switch_preamble_is_accepted():
    role, remainder, ambiguous = _role_declaration(
        "Ă, acuma schimbăm rolul. Sunt dispecer PPC. Câte tichete am și câte au risc de siguranță?"
    )
    assert role == "dispatcher" and not ambiguous and "Câte tichete" in remainder


def test_report_after_failed_first_turn_keeps_verified_default_role(demo_call, env):  # noqa: F811
    seen = []

    async def report(operations, actor, **kwargs):
        seen.append(actor.role)
        return {"reply": "Raportul PDF a fost livrat pe WhatsApp."}

    demo_call["entry"]["allow_voice_reports"] = True
    client = TestClient(
        create_app(
            service=env["conversation"],
            bindings=demo_call["bindings"],
            config_loader=lambda: demo_call["config"],
            report_sender=report,
        )
    )
    response = client.post(
        "/api/voice/turn",
        headers=demo_call["headers"],
        json={
            "caller_id": "+40700000000",
            "conversation_id": "synthetic-new-call",
            "message": "Trimite-mi raportul pe WhatsApp.",
        },
    )
    assert response.status_code == 200 and "livrat" in response.json()["reply"]
    assert seen == ["technician"] and not env["provider"].prompts


def test_abandoned_slow_turn_does_not_block_a_new_call(demo_call, env, monkeypatch):  # noqa: F811
    started = asyncio.Event()

    async def slow(*args, **kwargs):
        started.set()
        await asyncio.Event().wait()

    monkeypatch.setattr(env["conversation"], "chat", slow)
    from cyberpunks.channels import voice_briefs

    monkeypatch.setattr(voice_briefs, "answer_demo", demo_call["real_brief"])
    app = create_app(
        service=env["conversation"], bindings=demo_call["bindings"], config_loader=lambda: demo_call["config"]
    )

    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://synthetic") as client:
            first = asyncio.create_task(
                client.post(
                    "/api/voice/turn",
                    headers=demo_call["headers"],
                    json={
                        "caller_id": "+40700000000",
                        "conversation_id": "synthetic-abandoned",
                        "message": "Sunt tehnician. Detaliu necunoscut.",
                    },
                )
            )
            await asyncio.wait_for(started.wait(), 3)
            try:
                second = await client.post(
                    "/api/voice/turn",
                    headers=demo_call["headers"],
                    json={
                        "caller_id": "+40700000000",
                        "conversation_id": "synthetic-next-call",
                        "message": "Ă, sunt tehnician PPC. Ce am de făcut astăzi?",
                    },
                )
                assert second.status_code == 200 and any(
                    word in second.json()["reply"] for word in ("opriri", "aprobat")
                )
            finally:
                first.cancel()
                await asyncio.gather(first, return_exceptions=True)

    asyncio.run(run())
