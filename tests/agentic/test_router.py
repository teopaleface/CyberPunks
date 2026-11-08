import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from cyberpunks.agentic.router import create_router
from cyberpunks.agentic.task_store import TaskStore


@pytest.mark.parametrize(
    "role,goal", [("dispatcher", "analyze_queue"), ("technician", "route_brief"), ("customer", "case_brief")]
)
def test_tasks_are_private_and_resume_is_read_only(env, tmp_path, role, goal):
    store = TaskStore(tmp_path / "tasks.sqlite")
    app = FastAPI()
    app.include_router(create_router(env["service"], store))
    client = TestClient(app)
    headers = env["headers"](env[role])
    result = client.post("/api/conversation/tasks", headers=headers, json={"goal": goal})
    assert result.status_code == 200, result.text
    task = result.json()
    path = "/api/conversation/tasks/" + task["task_id"]
    assert client.get(path, headers=headers).json() == task
    assert client.post(path + "/resume", headers=headers).json() == task
    foreign = env["customer"] if role != "customer" else env["dispatcher"]
    assert client.get(path, headers=env["headers"](foreign)).status_code == 404
    assert client.get(path).status_code == 401


def test_old_snapshot_rejected_and_get_has_no_effect(env, tmp_path, monkeypatch):
    store = TaskStore(tmp_path / "tasks.sqlite")
    app = FastAPI()
    app.include_router(create_router(env["service"], store))
    client = TestClient(app)
    headers = env["headers"](env["dispatcher"])
    task = client.post("/api/conversation/tasks", headers=headers, json={"goal": "analyze_queue"}).json()

    def forbidden(*args, **kwargs):
        raise AssertionError("GET must not execute or observe operations")

    monkeypatch.setattr(env["service"], "command", forbidden)
    monkeypatch.setattr(env["service"], "confirm", forbidden)
    monkeypatch.setattr(env["service"], "observe_effect", forbidden)
    path = "/api/conversation/tasks/" + task["task_id"]
    assert client.get(path, headers=headers).status_code == 200
    original = env["service"].context

    def changed(*args, **kwargs):
        from copy import deepcopy

        context = deepcopy(original(*args, **kwargs))
        context["plan"]["version"] = "changed-version"
        return context

    monkeypatch.setattr(env["service"], "context", changed)
    assert client.get(path, headers=headers).status_code == 409
    assert client.post(path + "/resume", headers=headers).status_code == 409


def test_confirmed_resume_observes_real_effect(env, tmp_path, monkeypatch):
    store = TaskStore(tmp_path / "tasks.sqlite")
    app = FastAPI()
    app.include_router(create_router(env["service"], store))
    client = TestClient(app)
    headers = env["headers"](env["customer"])
    task = client.post(
        "/api/conversation/tasks",
        headers=headers,
        json={
            "goal": "prepare_operation",
            "action": "create_case",
            "data": {
                "connection_id": env["binding"]["connection_id"],
                "symptom": "Inverter stops at noon",
                "symptom_type": "meter",
            },
        },
    ).json()
    assert task["status"] == "awaiting_confirmation", task
    effect = env["service"].confirm(env["customer"], task["proposal"]["proposal_id"])

    def forbidden(*args, **kwargs):
        raise AssertionError("Resume must only observe")

    monkeypatch.setattr(env["service"], "confirm", forbidden)
    monkeypatch.setattr(env["service"], "command", forbidden)
    path = "/api/conversation/tasks/" + task["task_id"]
    assert client.get(path, headers=headers).json()["status"] == "awaiting_confirmation"
    resumed = client.post(path + "/resume", headers=headers)
    assert resumed.status_code == 200, resumed.text
    assert resumed.json()["status"] == "completed"
    assert resumed.json()["result"]["effect"]["command"] == effect


def test_resume_runs_same_durable_queued_task(env, tmp_path):
    from cyberpunks.agentic.contracts import TaskRequest

    service, actor = env["service"], env["dispatcher"]
    store = TaskStore(tmp_path / "resume.sqlite3")
    request = TaskRequest(goal="analyze_queue")
    task = store.create(actor, request, service.context(actor, "demo-vara")["plan"]["version"])
    assert store.request(actor, task.task_id) == request
    app = FastAPI()
    app.include_router(create_router(service, store))
    client = TestClient(app)
    response = client.post("/api/conversation/tasks/" + task.task_id + "/resume", headers=env["headers"](actor))
    assert response.status_code == 200, response.text
    assert response.json()["task_id"] == task.task_id
    assert response.json()["status"] == "completed"
    assert response.json()["result"]["complete"]


def test_case_version_change_invalidates_task_without_plan_change(env, tmp_path):
    from cyberpunks.agentic.contracts import TaskRequest
    from cyberpunks.agentic.coordinator import AgenticCoordinator

    s, actor = env["service"], env["customer"]
    proposal = s.prepare(
        actor,
        "create_case",
        {
            "connection_id": actor.connection_ids[0],
            "symptom": "Synthetic case version regression",
            "symptom_type": "voltage",
        },
        "demo-vara",
    )
    s.confirm(actor, proposal["proposal_id"])
    store = TaskStore(tmp_path / "case-version.sqlite3")
    task = AgenticCoordinator(s, store).run(actor, TaskRequest(goal="case_brief"))
    case = task.result["cases"][0]
    proposal = s.prepare(
        actor,
        "set_availability",
        {"case_id": case["case_id"], "start": "2025-07-08T10:00:00+03:00", "end": "2025-07-08T12:00:00+03:00"},
        "demo-vara",
    )
    s.confirm(actor, proposal["proposal_id"])
    assert s.context(actor, "demo-vara")["plan"]["version"] == task.plan_version
    app = FastAPI()
    app.include_router(create_router(s, store))
    client = TestClient(app)
    assert client.get("/api/conversation/tasks/" + task.task_id, headers=env["headers"](actor)).status_code == 409
