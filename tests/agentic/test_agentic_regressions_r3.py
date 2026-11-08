"""Agentic regressions on the complete historical source and synthetic operational cases.

Includes the five defects found in the read-only audit, now fixed and required to pass.
"""

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from math import ceil

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from cyberpunks.agentic.contracts import TaskRequest
from cyberpunks.agentic.coordinator import AgenticCoordinator
from cyberpunks.agentic.report_data import build_report_data
from cyberpunks.agentic.report_templates import render_report
from cyberpunks.agentic.router import create_router
from cyberpunks.agentic.task_store import TaskStore
from cyberpunks.operations.models import OperationError


def coordinator(env, tmp_path, name="tasks.sqlite3"):
    return AgenticCoordinator(env["service"], TaskStore(tmp_path / name))


def client_for(env, store):
    app = FastAPI()
    app.include_router(create_router(env["service"], store))
    return TestClient(app)


def count(env, table, where="1=1"):
    with env["service"].db.connect() as db:
        return db.execute(f"SELECT count(*) AS n FROM {table} WHERE {where}").fetchone()["n"]


def approve(env, crew_id=None):
    s, dispatcher = env["service"], env["dispatcher"]
    plan = s.context(dispatcher, "demo-vara")["plan"]
    data = {"plan_id": plan["plan_id"]}
    if crew_id:
        data["crew_id"] = crew_id
    proposal = s.prepare(dispatcher, "approve_plan", data, "demo-vara")
    s.confirm(dispatcher, proposal["proposal_id"])


def review_prepare_request(env, **extra):
    work = next(
        w
        for w in env["service"].context(env["dispatcher"], "demo-vara")["work_items"]
        if (w.get("decision") or {}).get("decision") == "human_review"
    )
    return TaskRequest(
        goal="prepare_operation",
        action="review_work_item",
        data={"work_item_id": work["work_item_id"], "decision": "defer", "note": "Synthetic r3 probe"},
        **extra,
    )


# ---------------------------------------------------------------- queue 25 vs first 8


def test_queue_is_every_human_review_item_not_a_first_page(env, tmp_path):
    s, d = env["service"], env["dispatcher"]
    context = s.context(d, "demo-vara")
    expected = [w["work_item_id"] for w in context["work_items"] if w["decision"]["decision"] == "human_review"]
    assert len(expected) > 8, "fixture must expose a queue larger than the old eight-item page"
    task = coordinator(env, tmp_path).run(d, TaskRequest(goal="analyze_queue"))
    result = task.result
    assert result["analyzed_ids"] == result["expected_ids"] == expected
    assert [row["work_item_id"] for row in result["items"]] == expected
    assert result["total"] == len(expected) == len(set(expected))
    # Every analyzed row names its recommendation, a reason and evidence from the same plan version.
    for row in result["items"]:
        assert row["recommendation"] and row["reason"]
        assert row["evidence"]["plan_version"] == context["plan"]["version"]
        assert row["evidence"]["source"]["work_item_id"] == row["work_item_id"]


def test_queue_report_renders_every_row_on_paginated_pages(env, tmp_path):
    d = env["dispatcher"]
    task = coordinator(env, tmp_path).run(d, TaskRequest(goal="analyze_queue"))
    context = env["service"].context(d, "demo-vara")
    data = build_report_data(context, task.result, "ro")
    assert len(data["rows"]) == task.result["total"]
    pages = render_report(data)
    assert len(pages) == ceil(task.result["total"] / 3)
    html = "".join(pages)
    for wid in task.result["analyzed_ids"]:
        assert f"Referință: {wid}" in html, wid


def test_queue_snapshot_matches_plan_decisions(env, tmp_path):
    """Queue coverage is computed from the full plan, independent of the work item order."""
    s, d = env["service"], env["dispatcher"]
    context = s.context(d, "demo-vara")
    plan = s.planner.view("demo-vara").plan()
    from_plan = {x["work_item_id"] for x in plan["decisions"] if x["decision"] == "human_review"}
    task = coordinator(env, tmp_path).run(d, TaskRequest(goal="analyze_queue"))
    assert set(task.result["analyzed_ids"]) == from_plan
    assert len(context["work_items"]) >= 600


# ---------------------------------------------------------------- role isolation


@pytest.mark.parametrize("role", ["customer", "technician"])
def test_only_dispatcher_can_start_queue_analysis_and_nothing_is_persisted(env, tmp_path, role):
    c = coordinator(env, tmp_path)
    with pytest.raises(PermissionError):
        c.run(env[role], TaskRequest(goal="analyze_queue", request_key="r3-" + role))
    assert c.store.list(env[role], "demo-vara") == []
    response = client_for(env, c.store).post(
        "/api/conversation/tasks", headers=env["headers"](env[role]), json={"goal": "analyze_queue"}
    )
    assert response.status_code == 404
    assert c.store.list(env[role], "demo-vara") == []


def test_customer_cannot_read_routes(env, tmp_path):
    approve(env)
    c = coordinator(env, tmp_path)
    with pytest.raises(PermissionError):
        c.run(env["customer"], TaskRequest(goal="route_brief"))


@pytest.mark.parametrize(
    "role,action,data",
    [
        ("customer", "approve_plan", {"plan_id": "x"}),
        ("customer", "review_work_item", {"work_item_id": "x", "decision": "defer"}),
        ("technician", "approve_plan", {"plan_id": "x"}),
        ("technician", "review_work_item", {"work_item_id": "x", "decision": "defer"}),
        ("technician", "create_case", {"connection_id": "x", "symptom": "synthetic"}),
        ("dispatcher", "record_verdict", {"work_item_id": "x", "outcome": "confirmed"}),
    ],
)
def test_prepare_refuses_actions_outside_the_role_and_creates_no_proposal(env, tmp_path, role, action, data):
    c = coordinator(env, tmp_path)
    before = count(env, "proposals")
    with pytest.raises(OperationError) as caught:
        c.run(env[role], TaskRequest(goal="prepare_operation", action=action, data=data))
    assert caught.value.status_code == 403
    assert count(env, "proposals") == before
    # The refused task is terminal and carries no proposal.
    (task,) = c.store.list(env[role], "demo-vara")
    assert task.status == "failed" and task.proposal is None


def test_dispatcher_without_explicit_permission_cannot_prepare_approval(env, tmp_path):
    weak = env["dispatcher"].model_copy(update={"permissions": []})
    c = coordinator(env, tmp_path)
    plan_id = env["service"].context(env["dispatcher"], "demo-vara")["plan"]["plan_id"]
    with pytest.raises(OperationError) as caught:
        c.run(weak, TaskRequest(goal="prepare_operation", action="approve_plan", data={"plan_id": plan_id}))
    assert caught.value.status_code == 403
    assert count(env, "proposals") == 0


def test_customer_brief_only_contains_own_cases_without_internal_command_ids(env, tmp_path):
    s, customer = env["service"], env["customer"]
    proposal = s.prepare(
        customer,
        "create_case",
        {"connection_id": customer.connection_ids[0], "symptom": "Synthetic r3 isolation", "symptom_type": "voltage"},
        "demo-vara",
    )
    s.confirm(customer, proposal["proposal_id"])
    other = customer.model_copy(update={"user_id": "customer-2"})
    c = coordinator(env, tmp_path)
    mine = c.run(customer, TaskRequest(goal="case_brief"))
    assert mine.status == "completed" and len(mine.result["cases"]) == 1
    # Same connection grants, different person: the other customer owns no case.
    theirs = c.run(other, TaskRequest(goal="case_brief"))
    assert theirs.status == "needs_information" and not theirs.result.get("cases")
    with pytest.raises(PermissionError):
        c.store.get(other, mine.task_id)
    # Selecting someone else's case id never reveals it.
    forged = c.run(other, TaskRequest(goal="case_brief", case_id=mine.result["cases"][0]["case_id"]))
    assert forged.status == "needs_information" and not forged.result.get("cases")
    blob = mine.model_dump_json()
    # Assessment provenance ids are part of the existing customer contract; command/finding/requester ids are not.
    for forbidden in ("command_id", "finding_id", "requester_id", "linked_case_versions"):
        assert forbidden not in blob, forbidden


def test_technician_route_is_limited_to_own_crew(env, tmp_path):
    approve(env)
    s, dispatcher, technician = env["service"], env["dispatcher"], env["technician"]
    all_routes = s.context(dispatcher, "demo-vara")["plan"]["routes"]
    task = coordinator(env, tmp_path).run(technician, TaskRequest(goal="route_brief"))
    assert task.status == "completed"
    assert {r["crew_id"] for r in task.result["routes"]} == {technician.crew_id}
    own = {s_["work_item_id"] for r in all_routes if r["crew_id"] == technician.crew_id for s_ in r["stops"]}
    assert {s_["work_item_id"] for r in task.result["routes"] for s_ in r["stops"]} == own
    # A technician with a different crew cannot open this task and sees only their own route.
    stranger = technician.model_copy(update={"crew_id": "crew-that-does-not-exist"})
    with pytest.raises(PermissionError):
        coordinator(env, tmp_path).store.get(stranger, task.task_id)
    empty = coordinator(env, tmp_path).run(stranger, TaskRequest(goal="route_brief"))
    assert empty.status == "needs_information"


def test_task_identity_binds_every_membership_field(env, tmp_path):
    c = coordinator(env, tmp_path)
    task = c.run(env["dispatcher"], TaskRequest(goal="analyze_queue"))
    for update in (
        {"user_id": "someone-else"},
        {"organization_id": "other-org"},
        {"role": "technician"},
        {"permissions": ["approve_plan"]},
        {"crew_id": "crew-x"},
    ):
        with pytest.raises(PermissionError):
            c.store.get(env["dispatcher"].model_copy(update=update), task.task_id)
        with pytest.raises(PermissionError):
            c.store.request(env["dispatcher"].model_copy(update=update), task.task_id)
    # Router: foreign actors get 404 on GET and resume, never the saved result.
    client = client_for(env, c.store)
    for role in ("customer", "technician"):
        for suffix, method in (("", client.get), ("/resume", client.post)):
            r = method("/api/conversation/tasks/" + task.task_id + suffix, headers=env["headers"](env[role]))
            assert r.status_code == 404, (role, suffix)
            assert "analyzed_ids" not in r.text


# ---------------------------------------------------------------- no implicit confirmations


def test_prepare_never_confirms_and_no_endpoint_in_task_flow_executes(env, tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Agentic flow must never confirm, recover or reconcile")

    for name in ("confirm", "recover", "command"):
        monkeypatch.setattr(env["service"], name, forbidden)
    c = coordinator(env, tmp_path)
    client = client_for(env, c.store)
    headers = env["headers"](env["dispatcher"])
    created = client.post(
        "/api/conversation/tasks",
        headers=headers,
        json={**review_prepare_request(env).model_dump(mode="json")},
    )
    assert created.status_code == 200, created.text
    task = created.json()
    assert task["status"] == "awaiting_confirmation" and task["proposal"]["requires_confirmation"] is True
    path = "/api/conversation/tasks/" + task["task_id"]
    for _ in range(3):
        assert client.get(path, headers=headers).json()["status"] == "awaiting_confirmation"
        resumed = client.post(path + "/resume", headers=headers).json()
        assert resumed["status"] == "awaiting_confirmation"
        assert "No operation was executed" in resumed["reply"]
    assert count(env, "commands") == 0 and count(env, "events") == 0
    assert (
        env["service"].observe_effect(env["dispatcher"], task["proposal"]["proposal_id"], "demo-vara")["command"]
        is None
    )


@pytest.mark.parametrize(
    "smuggled",
    [
        {"confirm": True},
        {"confirmed": True},
        {"command_id": "x"},
        {"proposal_id": "x"},
        {"actor": {"role": "dispatcher"}},
        {"role": "dispatcher"},
        {"permissions": ["approve_plan"]},
    ],
)
def test_data_cannot_smuggle_confirmation_or_identity(env, tmp_path, smuggled):
    c = coordinator(env, tmp_path)
    base = review_prepare_request(env)
    request = base.model_copy(update={"data": {**base.data, **smuggled}})
    with pytest.raises(OperationError) as caught:
        c.run(env["dispatcher"], request)
    assert caught.value.status_code == 422
    assert count(env, "commands") == 0 and count(env, "proposals") == 0


def test_task_request_rejects_identity_and_confirm_fields():
    for extra in ({"actor": {}}, {"confirm": True}, {"user_id": "x"}, {"role": "dispatcher"}, {"status": "completed"}):
        with pytest.raises(ValueError):
            TaskRequest(goal="analyze_queue", **extra)
    with pytest.raises(ValueError):
        TaskRequest(goal="confirm_operation")


@pytest.mark.parametrize("answer", ["yes", "da", "confirm", "approve it"])
def test_conversation_yes_prepares_but_never_executes(env, tmp_path, answer):
    """A model that turns 'yes' into a prepare intention still only yields an unconfirmed proposal."""
    import asyncio

    from cyberpunks.channels.conversation import ConversationService
    from cyberpunks.channels.models import ChatRequest, Intention, IntentionData

    plan_id = env["service"].context(env["dispatcher"], "demo-vara")["plan"]["plan_id"]
    data = dict.fromkeys(IntentionData.model_fields)
    data["plan_id"] = plan_id

    class Provider:
        async def turn(self, prompt):
            return (
                Intention(
                    kind="prepare", reply="Approved.", language="en", action="approve_plan", data=data, evidence=[]
                ),
                {"provider": "simulated", "model": "test", "tools_enabled": False},
            )

    result = asyncio.run(
        ConversationService(env["service"], Provider()).chat(env["dispatcher"], ChatRequest(message=answer))
    )
    assert result["provenance"]["write_executed"] is False
    assert result["proposal"]["requires_confirmation"] is True
    assert "Confirm" in result["reply"] and "Approved" not in result["reply"]
    assert count(env, "commands") == 0
    assert env["service"].context(env["dispatcher"], "demo-vara")["plan"]["approved"] is False


def test_conversation_task_intent_never_prepares_or_confirms(env, tmp_path):
    import asyncio

    from cyberpunks.channels.conversation import ConversationService
    from cyberpunks.channels.models import ChatRequest, Intention, IntentionData

    class Provider:
        async def turn(self, prompt):
            return (
                Intention(
                    kind="task",
                    task_goal="analyze_queue",
                    reply="x",
                    language="en",
                    action=None,
                    data=IntentionData(**dict.fromkeys(IntentionData.model_fields)),
                    evidence=[],
                ),
                {"provider": "simulated", "model": "test", "tools_enabled": False},
            )

    service = env["service"]
    result = asyncio.run(
        ConversationService(service, Provider()).chat(env["dispatcher"], ChatRequest(message="analyze the queue"))
    )
    assert result["task"]["status"] == "completed" and result["proposal"] is None
    assert result["provenance"]["write_executed"] is False
    assert count(env, "proposals") == 0 and count(env, "commands") == 0


# ---------------------------------------------------------------- resume and idempotency


def test_same_request_key_prepares_once_even_under_concurrency(env, tmp_path):
    c = coordinator(env, tmp_path)
    request = review_prepare_request(env, request_key="r3-single-proposal")
    with ThreadPoolExecutor(6) as pool:
        tasks = list(pool.map(lambda _: c.run(env["dispatcher"], request), range(12)))
    assert len({t.task_id for t in tasks}) == 1
    assert count(env, "proposals") == 1
    final = c.store.get(env["dispatcher"], tasks[0].task_id)
    assert final.status == "awaiting_confirmation" and final.proposal
    # Different payload under the same key is refused instead of silently reused.
    other = request.model_copy(update={"data": {**request.data, "note": "Synthetic different note"}})
    with pytest.raises(ValueError):
        c.run(env["dispatcher"], other)
    assert count(env, "proposals") == 1


def test_crash_between_prepare_and_save_resumes_without_duplicate_proposal(env, tmp_path):
    """A running task whose lease expired is re-run on resume; preparation must be idempotent."""
    s, dispatcher = env["service"], env["dispatcher"]
    store = TaskStore(tmp_path / "crash.sqlite3")
    request = review_prepare_request(env)  # deliberately no request_key
    version = s.context(dispatcher, "demo-vara")["plan"]["version"]
    task = store.create(dispatcher, request, version)
    token = store.claim(dispatcher, task.task_id, seconds=1)
    assert token
    # Simulated crash after operations.prepare but before the task row was updated.
    first = s.prepare(dispatcher, "review_work_item", {**request.data, "plan_version": version}, "demo-vara")
    with sqlite3.connect(store.path) as db:
        db.execute("UPDATE agent_tasks SET lease_until=0 WHERE id=?", (task.task_id,))
    client = client_for(env, store)
    response = client.post("/api/conversation/tasks/" + task.task_id + "/resume", headers=env["headers"](dispatcher))
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "awaiting_confirmation"
    assert body["proposal"]["proposal_id"] == first["proposal_id"]
    assert count(env, "proposals") == 1
    again = client.post("/api/conversation/tasks/" + task.task_id + "/resume", headers=env["headers"](dispatcher))
    assert again.json()["proposal"]["proposal_id"] == first["proposal_id"]
    assert count(env, "proposals") == 1


def test_live_lease_blocks_second_executor_and_resume_does_not_steal(env, tmp_path):
    s, dispatcher = env["service"], env["dispatcher"]
    store = TaskStore(tmp_path / "lease.sqlite3")
    request = TaskRequest(goal="analyze_queue")
    task = store.create(dispatcher, request, s.context(dispatcher, "demo-vara")["plan"]["version"])
    token = store.claim(dispatcher, task.task_id, seconds=60)
    response = client_for(env, store).post(
        "/api/conversation/tasks/" + task.task_id + "/resume", headers=env["headers"](dispatcher)
    )
    assert response.status_code == 200
    assert response.json()["status"] == "running" and not response.json()["result"]
    # The legitimate holder can still finish.
    done = store.update(dispatcher, task.task_id, claim_token=token, status="completed")
    assert done.status == "completed"


def test_confirmed_task_resume_is_idempotent_and_terminal(env, tmp_path):
    s, dispatcher = env["service"], env["dispatcher"]
    c = coordinator(env, tmp_path)
    task = c.run(dispatcher, review_prepare_request(env))
    s.confirm(dispatcher, task.proposal["proposal_id"])
    client = client_for(env, c.store)
    path = "/api/conversation/tasks/" + task.task_id
    first = client.post(path + "/resume", headers=env["headers"](dispatcher))
    assert first.status_code == 200, first.text
    assert first.json()["status"] == "completed"
    commands = count(env, "commands")
    # A further resume is a no-op and cannot be turned back into awaiting_confirmation.
    for _ in range(2):
        again = client.post(path + "/resume", headers=env["headers"](dispatcher))
        assert again.status_code == 200 and again.json()["status"] == "completed"
    assert count(env, "commands") == commands == 1


def _force_command_status(env, proposal_id, status):
    import json

    with env["service"].db.connect() as db:
        row = db.execute("SELECT command_id FROM proposals WHERE proposal_id=?", (proposal_id,)).fetchone()
        body = json.loads(
            db.execute("SELECT body FROM commands WHERE command_id=?", (row["command_id"],)).fetchone()["body"]
        )
        body["status"] = status
        db.execute(
            "UPDATE commands SET status=?, body=? WHERE command_id=?", (status, json.dumps(body), row["command_id"])
        )
        db.commit()


def test_needs_reconciliation_task_completes_after_command_succeeds(env, tmp_path):
    s, dispatcher = env["service"], env["dispatcher"]
    c = coordinator(env, tmp_path)
    task = c.run(dispatcher, review_prepare_request(env))
    s.confirm(dispatcher, task.proposal["proposal_id"])
    _force_command_status(env, task.proposal["proposal_id"], "reconciling")
    client = client_for(env, c.store)
    path = "/api/conversation/tasks/" + task.task_id + "/resume"
    assert client.post(path, headers=env["headers"](dispatcher)).json()["status"] == "needs_reconciliation"
    _force_command_status(env, task.proposal["proposal_id"], "succeeded")
    assert client.post(path, headers=env["headers"](dispatcher)).json()["status"] == "completed"


def test_expired_unconfirmed_proposal_is_not_reported_as_awaiting_confirmation(env, tmp_path):
    import json

    s, dispatcher = env["service"], env["dispatcher"]
    c = coordinator(env, tmp_path)
    task = c.run(dispatcher, review_prepare_request(env))
    with s.db.connect() as db:
        row = db.execute("SELECT body FROM proposals WHERE proposal_id=?", (task.proposal["proposal_id"],)).fetchone()
        body = json.loads(row["body"])
        body["expires_at"] = (datetime.now(UTC) - timedelta(minutes=1)).isoformat()
        db.execute("UPDATE proposals SET body=? WHERE proposal_id=?", (json.dumps(body), task.proposal["proposal_id"]))
        db.commit()
    with pytest.raises(OperationError) as caught:
        s.confirm(dispatcher, task.proposal["proposal_id"])
    assert caught.value.code == "proposal_expired"
    response = client_for(env, c.store).post(
        "/api/conversation/tasks/" + task.task_id + "/resume", headers=env["headers"](dispatcher)
    )
    assert response.json()["status"] != "awaiting_confirmation"
    assert "Awaiting confirmation" not in response.json()["reply"]


def test_plan_change_invalidates_every_unconfirmed_or_completed_task(env, tmp_path):
    s, dispatcher = env["service"], env["dispatcher"]
    c = coordinator(env, tmp_path)
    queue = c.run(dispatcher, TaskRequest(goal="analyze_queue"))
    pending = c.run(dispatcher, review_prepare_request(env))
    approve(env)  # changes the plan version
    client = client_for(env, c.store)
    for task in (queue, pending):
        path = "/api/conversation/tasks/" + task.task_id
        assert client.get(path, headers=env["headers"](dispatcher)).status_code == 409
        assert client.post(path + "/resume", headers=env["headers"](dispatcher)).status_code == 409
    # The stale proposal can no longer be confirmed either.
    with pytest.raises(OperationError) as caught:
        s.confirm(dispatcher, pending.proposal["proposal_id"])
    assert caught.value.code == "stale_plan"
    # Fresh work starts from a new task on the current plan.
    fresh = c.run(dispatcher, TaskRequest(goal="analyze_queue"))
    assert fresh.status == "completed" and fresh.plan_version != queue.plan_version


# ---------------------------------------------------------------- approved route correctness


def test_unapproved_route_for_every_role_yields_no_stops(env, tmp_path):
    c = coordinator(env, tmp_path)
    for role in ("technician", "dispatcher"):
        task = c.run(env[role], TaskRequest(goal="route_brief"))
        assert task.status == "needs_information" and not task.result.get("routes"), role


def test_whole_plan_approval_exposes_routes_with_titles_and_next_stop(env, tmp_path):
    approve(env)
    s, technician = env["service"], env["technician"]
    context = s.context(technician, "demo-vara")
    assert context["next_stop_status"] == "approved_plan"
    task = coordinator(env, tmp_path).run(technician, TaskRequest(goal="route_brief"))
    assert task.status == "completed"
    (route,) = task.result["routes"]
    stops = route["stops"]
    assert stops and all(st["title"] and st["eta"] for st in stops)
    assert [st["seq"] for st in stops] == sorted(st["seq"] for st in stops)
    assert task.result["next_stop"]["work_item_id"] == stops[0]["work_item_id"]
    assert task.result["next_stop_status"] == "approved_plan"
    assert "aprobată" in task.reply and stops[0]["title"] in task.reply


def test_crew_level_approval_only_releases_that_crew(env, tmp_path):
    s, dispatcher, technician = env["service"], env["dispatcher"], env["technician"]
    routes = s.context(dispatcher, "demo-vara")["plan"]["routes"]
    if len(routes) < 2:
        pytest.skip("needs a plan with at least two crews")
    approve(env, technician.crew_id)
    c = coordinator(env, tmp_path)
    own = c.run(technician, TaskRequest(goal="route_brief"))
    assert own.status == "completed"
    seen = c.run(dispatcher, TaskRequest(goal="route_brief"))
    assert seen.status == "completed"
    assert {r["crew_id"] for r in seen.result["routes"]} == {technician.crew_id}
    # A technician from another crew still has no approved route.
    other_crew = next(r["crew_id"] for r in routes if r["crew_id"] != technician.crew_id)
    other = technician.model_copy(update={"crew_id": other_crew})
    assert c.run(other, TaskRequest(goal="route_brief")).status == "needs_information"


def test_replan_after_approval_revokes_the_approved_route(env, tmp_path):
    approve(env)
    s, dispatcher, technician = env["service"], env["dispatcher"], env["technician"]
    c = coordinator(env, tmp_path)
    approved = c.run(technician, TaskRequest(goal="route_brief"))
    assert approved.status == "completed"
    review = c.run(dispatcher, review_prepare_request(env))
    s.confirm(dispatcher, review.proposal["proposal_id"])
    after = c.run(technician, TaskRequest(goal="route_brief"))
    # Either the recalculated route needs approval again or the new plan is still validly approved,
    # but an old approval must never be applied to a changed route signature.
    context = s.context(technician, "demo-vara")
    if context["next_stop_status"] == "awaiting_approval":
        assert after.status == "needs_information" and not after.result.get("routes")
    else:
        assert after.status == "completed" and after.plan_version == context["plan"]["version"]
    client = client_for(env, c.store)
    stale = client.get("/api/conversation/tasks/" + approved.task_id, headers=env["headers"](technician))
    assert stale.status_code == 409


def test_technician_report_labels_proposed_vs_approved_and_uses_task_routes(env, tmp_path):
    s, technician = env["service"], env["technician"]
    context = s.context(technician, "demo-vara")
    proposed = build_report_data(context)
    assert proposed["state"] == "proposed"
    assert "Propunere, neaplicată" in render_report(proposed)[0]
    approve(env)
    context = s.context(technician, "demo-vara")
    data = build_report_data(context)
    assert data["state"] == "approved" and data["rows"]
    assert "Traseu aprobat" in render_report(data)[0]


def test_technician_route_report_shows_where_to_go(env, tmp_path):
    approve(env)
    technician = env["technician"]
    task = coordinator(env, tmp_path).run(technician, TaskRequest(goal="route_brief"))
    context = env["service"].context(technician, "demo-vara")
    context = {**context, "plan": {**context["plan"], "routes": task.result["routes"]}}
    data = build_report_data(context)
    assert all(row.get("title") for row in data["rows"]), data["rows"][:1]


def test_next_stop_skips_a_stop_that_already_has_a_finding(env, tmp_path):
    approve(env)
    s, technician = env["service"], env["technician"]
    c = coordinator(env, tmp_path)
    visited = c.run(technician, TaskRequest(goal="route_brief")).result["next_stop"]["work_item_id"]
    task = c.run(
        technician,
        TaskRequest(
            goal="prepare_operation", action="record_verdict", data={"work_item_id": visited, "outcome": "confirmed"}
        ),
    )
    s.confirm(technician, task.proposal["proposal_id"])
    after = c.run(technician, TaskRequest(goal="route_brief"))
    assert after.status == "completed"
    nxt = after.result.get("next_stop")
    assert nxt is None or nxt["work_item_id"] != visited


def test_concurrent_resumes_of_a_confirmed_task_all_report_the_same_result(env, tmp_path):
    s, dispatcher = env["service"], env["dispatcher"]
    c = coordinator(env, tmp_path)
    task = c.run(dispatcher, review_prepare_request(env))
    s.confirm(dispatcher, task.proposal["proposal_id"])
    path = "/api/conversation/tasks/" + task.task_id + "/resume"

    def resume(_):
        return client_for(env, c.store).post(path, headers=env["headers"](dispatcher))

    with ThreadPoolExecutor(8) as pool:
        responses = list(pool.map(resume, range(8)))
    assert {r.status_code for r in responses} == {200}, [(r.status_code, r.text[:80]) for r in responses]
    assert {r.json()["status"] for r in responses} == {"completed"}
    assert count(env, "commands") == 1
