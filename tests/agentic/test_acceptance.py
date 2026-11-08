import pytest

from cyberpunks.agentic.contracts import TaskRequest
from cyberpunks.agentic.coordinator import AgenticCoordinator
from cyberpunks.agentic.task_store import TaskStore


def coordinator(env, tmp_path):
    return AgenticCoordinator(env["service"], TaskStore(tmp_path / "tasks.sqlite3"))


def test_complete_queue_on_full_source(env, tmp_path):
    service, actor = env["service"], env["dispatcher"]
    before = service.context(actor, "demo-vara")
    expected = {w["work_item_id"] for w in before["work_items"] if w["decision"]["decision"] == "human_review"}
    assert len(before["work_items"]) >= 600 and len(expected) > 8
    task = coordinator(env, tmp_path).run(actor, TaskRequest(goal="analyze_queue"))
    assert task.status == "completed"
    assert set(task.result["analyzed_ids"]) == expected
    assert task.result["total"] == len(expected)
    assert service.context(actor, "demo-vara")["plan"]["version"] == before["plan"]["version"]
    with pytest.raises(PermissionError):
        coordinator(env, tmp_path).run(env["customer"], TaskRequest(goal="analyze_queue"))


def test_confirm_then_passively_observe(env, tmp_path, monkeypatch):
    service, actor = env["service"], env["customer"]
    task = coordinator(env, tmp_path).run(
        actor,
        TaskRequest(
            goal="prepare_operation",
            action="create_case",
            data={
                "connection_id": env["binding"]["connection_id"],
                "symptom": "Synthetic agentic acceptance: inverter stops",
                "symptom_type": "voltage",
            },
            request_key="synthetic-acceptance-case",
        ),
    )
    assert task.status == "awaiting_confirmation"
    assert service.observe_effect(actor, task.proposal["proposal_id"], "demo-vara")["command"] is None
    command = service.confirm(actor, task.proposal["proposal_id"])
    monkeypatch.setattr(service, "command", lambda *args: pytest.fail("Passive observation must not reconcile"))
    for _ in range(2):
        observed = service.observe_effect(actor, task.proposal["proposal_id"], "demo-vara")
        assert observed["command"]["command_id"] == command["command_id"]
    assert len(service.context(actor, "demo-vara")["cases"]) == 1
    with pytest.raises(__import__("cyberpunks.operations.models", fromlist=["OperationError"]).OperationError):
        service.observe_effect(env["dispatcher"], task.proposal["proposal_id"], "demo-vara")


def test_unapproved_route_is_not_dispatched(env, tmp_path):
    task = coordinator(env, tmp_path).run(env["technician"], TaskRequest(goal="route_brief"))
    assert task.status == "needs_information"
    assert not task.result.get("routes")


def test_task_retry_and_membership_change(env, tmp_path):
    c = coordinator(env, tmp_path)
    a = env["dispatcher"]
    r = TaskRequest(goal="analyze_queue", request_key="synthetic-queue")
    first = c.run(a, r)
    second = c.run(a, r)
    assert first.task_id == second.task_id
    with pytest.raises(PermissionError):
        c.store.get(a.model_copy(update={"permissions": []}), first.task_id)


def test_approved_route_and_actual_review_effect_remain_observable(env, tmp_path):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from cyberpunks.agentic.router import create_router

    s, dispatcher = env["service"], env["dispatcher"]
    before = s.context(dispatcher, "demo-vara")
    approval = s.prepare(dispatcher, "approve_plan", {"plan_id": before["plan"]["plan_id"]}, "demo-vara")
    s.confirm(dispatcher, approval["proposal_id"])
    c = coordinator(env, tmp_path)
    route = c.run(env["technician"], TaskRequest(goal="route_brief"))
    assert route.status == "completed" and route.result["routes"]
    assert all("title" in stop for r in route.result["routes"] for stop in r["stops"])
    work = next(
        w for w in s.context(dispatcher, "demo-vara")["work_items"] if w["decision"]["decision"] == "human_review"
    )
    task = c.run(
        dispatcher,
        TaskRequest(
            goal="prepare_operation",
            action="review_work_item",
            data={"work_item_id": work["work_item_id"], "decision": "defer", "note": "Synthetic integration decision"},
        ),
    )
    s.confirm(dispatcher, task.proposal["proposal_id"])
    app = FastAPI()
    app.include_router(create_router(s, c.store))
    client = TestClient(app)
    response = client.post("/api/conversation/tasks/" + task.task_id + "/resume", headers=env["headers"](dispatcher))
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "completed"
    assert response.json()["result"]["effect"]["command"]["status"] == "succeeded"


def test_runtime_mounts_private_task_routes(env, tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from cyberpunks import runtime

    monkeypatch.setattr("cyberpunks.operations.service.get_service", lambda: env["service"])
    monkeypatch.setenv("DAYBREAK_OPERATIONS_OUTPUTS", str(env["root"]))
    app = runtime.create_app()
    client = TestClient(app)
    path = "/api/conversation/tasks"
    assert client.post(path, json={"goal": "analyze_queue"}).status_code == 401
    response = client.post(path, headers=env["headers"](env["dispatcher"]), json={"goal": "analyze_queue"})
    assert response.status_code == 200, response.text
    assert response.json()["result"]["complete"] is True
