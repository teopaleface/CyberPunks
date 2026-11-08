"""Synthetic queue-only inputs; no operational data, services or external effects."""

import asyncio
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest

from cyberpunks.channels.voice_jobs import VoiceJobFailed, VoiceJobs
from cyberpunks.operations.models import Actor


@pytest.fixture
def actor():
    return Actor(user_id="synthetic-voice", organization_id="synthetic-org", role="dispatcher")


@pytest.fixture
def payload():
    return {"conversation_id": "synthetic-call", "caller": "synthetic-caller", "destination": "synthetic-destination"}


def test_durable_idempotency_and_conflicts(tmp_path, actor, payload):
    path = tmp_path / "voice-jobs.sqlite3"
    store = VoiceJobs(path)
    first = store.submit(actor, "report", payload, "synthetic-event")
    restarted = VoiceJobs(path)
    assert restarted.submit(actor, "report", dict(reversed(list(payload.items()))), "synthetic-event") == first
    assert first["verifiedActor"] == actor.model_dump(mode="json")
    assert first["payload"] == payload and first["attempts"] == 0
    assert path.stat().st_mode & 0o777 == 0o600
    for changed_actor, kind, changed_payload in (
        (actor.model_copy(update={"role": "customer"}), "report", payload),
        (actor, "dispatch", payload),
        (actor, "report", {**payload, "destination": "synthetic-other"}),
    ):
        with pytest.raises(ValueError, match="conflicts"):
            restarted.submit(changed_actor, kind, changed_payload, "synthetic-event")
    assert restarted.get(first["job_id"]) == first


def test_atomic_concurrent_submission(tmp_path, actor, payload):
    path = tmp_path / "voice-jobs.sqlite3"
    stores = [VoiceJobs(path) for _ in range(8)]
    with ThreadPoolExecutor(max_workers=8) as pool:
        jobs = list(pool.map(lambda s: s.submit(actor, "dispatch", payload, "synthetic-event"), stores))
    assert len({j["job_id"] for j in jobs}) == 1
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT count(*) FROM voice_jobs").fetchone()[0] == 1


def test_latest_is_actor_and_conversation_scoped(tmp_path, actor, payload):
    store = VoiceJobs(tmp_path / "voice-jobs.sqlite3", clock=lambda: 10)
    first = store.submit(actor, "report", payload, "synthetic-1")
    second = store.submit(actor, "dispatch", payload, "synthetic-2")
    other = actor.model_copy(update={"organization_id": "synthetic-other"})
    store.submit(other, "report", payload, "synthetic-3")
    store.submit(actor, "report", {**payload, "conversation_id": "synthetic-other"}, "synthetic-4")
    assert store.latest(actor, payload["conversation_id"])["job_id"] == second["job_id"]
    assert store.latest(actor, "missing") is None
    assert store.get(first["job_id"], actor=other) is None
    assert store.get(first["job_id"], actor=actor)["job_id"] == first["job_id"]
    assert store.get("missing") is None


def test_concurrent_drainers_claim_once_and_dont_hold_sqlite(tmp_path, actor, payload):
    path = tmp_path / "voice-jobs.sqlite3"
    stores = [VoiceJobs(path) for _ in range(6)]
    queued = stores[0].submit(actor, "dispatch", payload, "synthetic-1")

    async def scenario():
        started, release = asyncio.Event(), asyncio.Event()
        calls = []

        async def handler(job):
            calls.append(job["job_id"])
            started.set()
            await release.wait()
            return {"reply": "synthetic-result", "nested": {"rows": [1, 2]}}

        owner = asyncio.create_task(stores[0].drain_one(handler))
        await started.wait()
        others = await asyncio.gather(*(s.drain_one(handler) for s in stores[1:]))
        assert others == [None] * 5
        # A second caller can submit while the long-running handler is waiting.
        new = stores[1].submit(actor, "report", payload, "synthetic-2")
        assert new["status"] == "queued"
        release.set()
        done = await owner
        assert calls == [queued["job_id"]]
        assert done["status"] == "done"
        assert done["result"]["nested"] == {"rows": [1, 2]}
        assert done["lease_token"] is None
        assert VoiceJobs(path).submit(actor, "dispatch", payload, "synthetic-1") == done

    asyncio.run(scenario())


def test_restart_preserves_live_lease_then_recovers_and_fences(tmp_path, actor, payload):
    now = [100.0]
    path = tmp_path / "voice-jobs.sqlite3"
    store = VoiceJobs(path, lease_seconds=10, clock=lambda: now[0])
    queued = store.submit(actor, "report", payload, "synthetic-event")
    claimed = store._claim()
    restarted = VoiceJobs(path, lease_seconds=10, clock=lambda: now[0])
    assert restarted.recover_expired() == 0
    assert restarted._claim() is None
    forged = {**claimed, "lease_token": "synthetic-stale-token"}
    assert not store._finish(forged, "done", result={})
    assert not store._renew(forged)
    now[0] = 110.0
    assert not store._finish(claimed, "done", result={})
    assert not store._renew(claimed)
    assert restarted.recover_expired() == 1
    assert not store._finish(claimed, "done", result={})
    job = restarted.get(queued["job_id"])
    assert job["status"] == "needs_reconciliation"
    assert job["error"] == {"code": "lease_expired"}
    assert job["lease_token"] is None and job["lease_until"] is None
    assert restarted.recover_expired() == 0
    assert restarted._claim() is None


def test_stale_actor_is_reauthorized_by_handler_before_effect(tmp_path, actor, payload):
    store = VoiceJobs(tmp_path / "voice-jobs.sqlite3")
    store.submit(actor, "dispatch", payload, "synthetic-event")
    current = actor.model_copy(update={"role": "customer"})
    effects = []

    async def handler(job):
        snapshot = Actor.model_validate(job["verifiedActor"])
        if snapshot != current:
            raise VoiceJobFailed("actor_changed")
        effects.append("synthetic-effect")
        return {}

    result = asyncio.run(store.drain_one(handler))
    assert result["status"] == "failed"
    assert result["error"] == {"code": "actor_changed"}
    assert not effects
    assert asyncio.run(store.drain_one(handler)) is None


@pytest.mark.parametrize("outcome", ["unknown", "sending", "needs_reconciliation", "failed", "delivered"])
def test_result_states_survive_restart(tmp_path, actor, payload, outcome):
    path = tmp_path / "voice-jobs.sqlite3"
    store = VoiceJobs(path)
    queued = store.submit(actor, "report", payload, "synthetic-event")

    async def handler(job):
        return {"status": outcome, "receipt": {"id": "synthetic-receipt"}}

    job = asyncio.run(store.drain_one(handler))
    expected = "done" if outcome == "delivered" else "failed" if outcome == "failed" else "needs_reconciliation"
    assert job["status"] == expected
    assert VoiceJobs(path).get(queued["job_id"]) == job
    assert job["result"] == {"status": outcome, "receipt": {"id": "synthetic-receipt"}}
    assert asyncio.run(store.drain_one(handler)) is None


def test_cancellation_records_unknown_and_leaves_next_caller_workable(tmp_path, actor, payload):
    path = tmp_path / "voice-jobs.sqlite3"
    store = VoiceJobs(path)
    first = store.submit(actor, "report", payload, "synthetic-1")
    second = store.submit(actor, "dispatch", {**payload, "conversation_id": "synthetic-next"}, "synthetic-2")

    async def scenario():
        started = asyncio.Event()

        async def slow(job):
            started.set()
            await asyncio.Event().wait()

        task = asyncio.create_task(store.drain_one(slow))
        await started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert store.get(first["job_id"])["status"] == "needs_reconciliation"
        assert store.get(first["job_id"])["error"] == {"code": "cancelled"}

        async def next_handler(job):
            return {"reply": "synthetic-next-result"}

        result = await VoiceJobs(path).drain_one(next_handler)
        assert result["job_id"] == second["job_id"] and result["status"] == "done"
        assert await store.drain_one(next_handler) is None

    asyncio.run(scenario())


@pytest.mark.parametrize("result", ["exception", "invalid_json", "wrong_type"])
def test_uncertain_failures_are_not_retried_or_leaked(tmp_path, actor, payload, result):
    store = VoiceJobs(tmp_path / "voice-jobs.sqlite3")
    store.submit(actor, "report", payload, "synthetic-event")

    async def handler(job):
        if result == "exception":
            raise RuntimeError("synthetic-private-message-must-not-leak")
        if result == "invalid_json":
            return {"value": float("nan")}
        return []

    job = asyncio.run(store.drain_one(handler))
    assert job["status"] == "needs_reconciliation"
    assert "synthetic-private-message" not in json.dumps(job)
    assert asyncio.run(store.drain_one(handler)) is None


def test_heartbeat_extends_long_operation(tmp_path, actor, payload):
    now = [0.0]
    store = VoiceJobs(tmp_path / "voice-jobs.sqlite3", lease_seconds=0.09, clock=lambda: now[0])
    queued = store.submit(actor, "dispatch", payload, "synthetic-event")

    async def handler(job):
        # Real event-loop waits allow periodic heartbeats; logical time controls expiry.
        for _ in range(4):
            now[0] += 0.04
            await asyncio.sleep(0.07)
            assert store.recover_expired() == 0
        return {"reply": "synthetic-long-operation"}

    done = asyncio.run(store.drain_one(handler))
    assert done["status"] == "done" and done["job_id"] == queued["job_id"]


def test_lost_lease_cancels_handler_and_fences_result(tmp_path, actor, payload):
    now = [0.0]
    store = VoiceJobs(tmp_path / "voice-jobs.sqlite3", lease_seconds=0.06, clock=lambda: now[0])
    queued = store.submit(actor, "dispatch", payload, "synthetic-event")
    cancelled = []

    async def handler(job):
        now[0] = 100
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.append(True)

    job = asyncio.run(store.drain_one(handler))
    assert job["status"] == "needs_reconciliation"
    assert job["error"] == {"code": "lease_expired"}
    assert cancelled and store.get(queued["job_id"]) == job


@pytest.mark.parametrize(
    "kind,payload,key",
    [
        ("incident", {"conversation_id": "synthetic"}, "synthetic"),
        ("report", {}, "synthetic"),
        ("report", {"conversation_id": ""}, "synthetic"),
        ("dispatch", {"conversation_id": "synthetic"}, ""),
    ],
)
def test_invalid_submission(tmp_path, actor, kind, payload, key):
    store = VoiceJobs(tmp_path / "voice-jobs.sqlite3")
    with pytest.raises(ValueError):
        store.submit(actor, kind, payload, key)
