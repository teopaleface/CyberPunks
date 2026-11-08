import asyncio

from cyberpunks.channels.voice_jobs import VoiceJobs


def test_rephrased_requests_coalesce_durably_and_keep_both_call_references(tmp_path):
    store = VoiceJobs(tmp_path / "synthetic.sqlite3")
    actor = {"user_id": "synthetic-owner", "role": "technician"}
    first = store.submit(
        actor, "report", {"conversation_id": "call-one", "destination": "synthetic"}, "event-one", coalesce=True
    )
    second = store.submit(
        actor, "report", {"conversation_id": "call-two", "destination": "synthetic"}, "event-two", coalesce=True
    )
    assert second["job_id"] == first["job_id"]
    reopened = VoiceJobs(store.path)
    assert reopened.latest(actor, "call-two")["job_id"] == first["job_id"]
    asyncio.run(reopened.drain_one(lambda _: asyncio.sleep(0, result={"status": "delivered", "reply": "Livrat."})))
    assert (
        reopened.submit(
            actor, "report", {"conversation_id": "call-two", "destination": "synthetic"}, "event-two", coalesce=True
        )["status"]
        == "done"
    )
    assert reopened.latest(actor)["status"] == "done"


def test_nonterminal_handler_outcome_is_never_marked_done(tmp_path):
    store = VoiceJobs(tmp_path / "synthetic.sqlite3")
    store.submit({"user_id": "synthetic"}, "dispatch", {"conversation_id": "call"}, "event")
    result = asyncio.run(store.drain_one(lambda _: asyncio.sleep(0, result={"status": "running"})))
    assert result["status"] == "needs_reconciliation"


def test_report_status_reads_the_verified_delivery_callback_without_sending(tmp_path):
    import hashlib
    import sqlite3

    from cyberpunks.channels.voice_reports import observe_voice_report

    path = tmp_path / "synthetic-whatsapp.sqlite3"
    eid = hashlib.sha256(b"voice-report:synthetic-event").hexdigest()
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE outbound(event_id TEXT, kind TEXT, state TEXT)")
        db.execute("INSERT INTO outbound VALUES(?,?,?)", (eid, "document:synthetic", "delivered"))
    assert "a fost livrat" in observe_voice_report("synthetic-event", path)["reply"]
    assert observe_voice_report("other-event", path) is None
