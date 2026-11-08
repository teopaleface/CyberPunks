from concurrent.futures import ThreadPoolExecutor

import pytest

from cyberpunks.agentic.contracts import TaskRequest
from cyberpunks.agentic.task_store import TaskStore
from cyberpunks.operations.models import Actor


def test_retry_restart_claim_and_membership(tmp_path):
    path = tmp_path / "tasks.db"
    store = TaskStore(path)
    actor = Actor(user_id="synthetic", role="dispatcher", organization_id="synthetic")
    req = TaskRequest(goal="analyze_queue", request_key="synthetic")
    with ThreadPoolExecutor(4) as pool:
        views = list(pool.map(lambda _: store.create(actor, req, "v1"), range(8)))
    assert len({v.task_id for v in views}) == 1
    task = views[0]
    store = TaskStore(path)
    token = store.claim(actor, task.task_id)
    assert token and store.claim(actor, task.task_id) is None
    with pytest.raises(ValueError):
        store.update(actor, task.task_id, status="completed")
    store.update(actor, task.task_id, claim_token=token, status="cancelled")
    assert store.get(actor, task.task_id).status == "cancelled"
    with pytest.raises(PermissionError):
        store.get(actor.model_copy(update={"role": "customer"}), task.task_id)
    with pytest.raises(ValueError):
        store.create(actor, req.model_copy(update={"language": "en"}), "v1")


def test_real_membership_expiry_and_concurrent_reclaim(env, tmp_path):
    import time

    store = TaskStore(tmp_path / "real-tasks.db")
    for role in ("customer", "technician", "dispatcher"):
        actor = env[role]
        context = env["service"].context(actor, "demo-vara")
        task = store.create(actor, TaskRequest(goal="analyze_queue"), context["plan"]["version"])
        old = store.claim(actor, task.task_id, seconds=0.01)
        time.sleep(0.03)
        with pytest.raises(ValueError):
            store.update(actor, task.task_id, claim_token=old, status="completed")
        with ThreadPoolExecutor(8) as pool:
            tokens = list(pool.map(lambda _, actor=actor, task=task: store.claim(actor, task.task_id), range(16)))
        winners = [t for t in tokens if t]
        assert len(winners) == 1
        with pytest.raises(ValueError):
            store.update(actor, task.task_id, claim_token=old, status="completed")
        store.update(actor, task.task_id, claim_token=winners[0], status="completed")
        with pytest.raises(ValueError):
            store.update(actor, task.task_id, claim_token=winners[0], status="running")


def test_invalid_transition(env, tmp_path):
    store = TaskStore(tmp_path / "transitions.db")
    actor = env["dispatcher"]
    context = env["service"].context(actor, "demo-vara")
    task = store.create(actor, TaskRequest(goal="analyze_queue"), context["plan"]["version"])
    with pytest.raises(ValueError):
        store.update(actor, task.task_id, status="completed")
