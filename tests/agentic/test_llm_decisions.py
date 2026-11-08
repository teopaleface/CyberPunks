"""LLM output is explicitly simulated; operations use a fresh full real-data copy."""

import asyncio
import json
import sqlite3
from copy import deepcopy

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from cyberpunks.agentic.contracts import TaskRequest
from cyberpunks.agentic.llm_decisions import (
    LEASE_SECONDS,
    QueueDecisions,
    prepare_recommendation,
    recommend_queue,
    validate_decisions,
)
from cyberpunks.agentic.queue_analysis import analyze_queue
from cyberpunks.agentic.router import create_router
from cyberpunks.agentic.snapshots import authorized_snapshot
from cyberpunks.agentic.task_store import TaskStore
from cyberpunks.channels.conversation import SYSTEM, ConversationService
from cyberpunks.channels.models import ChannelError, ChatRequest, Intention, IntentionData


class SimulatedDecisionProvider:
    def __init__(self, choice="defer", mutation=None, callback=None):
        self.choice, self.mutation, self.callback = choice, mutation, callback
        self.prompts = []
        self.turns = []

    async def structured(self, prompt, schema):
        self.prompts.append(prompt)
        assert schema is QueueDecisions
        payload = json.loads(prompt.split("\nINPUT JSON:\n", 1)[1])
        rows = []
        for item in payload["review_queue"]:
            source = item["source"]
            rows.append(
                {
                    "work_item_id": item["work_item_id"],
                    "suggested_decision": self.choice if source["assessment"]["status"] == "available" else None,
                    "agent_reason": "The capacity constraint needs dispatcher review.",
                    "evidence": [
                        {
                            "path": item["source_path"] + "/assessment/status",
                            "value_json": json.dumps(source["assessment"]["status"]),
                        },
                        {
                            "path": item["source_path"] + "/decision/rule_id",
                            "value_json": json.dumps(source["decision"]["rule_id"]),
                        },
                    ],
                }
            )
        if self.mutation:
            self.mutation(rows, payload)
        if self.callback:
            await self.callback()
        return schema.model_validate({"items": rows}), {
            "provider": "simulated-decision-provider",
            "model": "synthetic-model",
            "tools_enabled": False,
        }

    async def turn(self, prompt):
        self.turns.append(prompt)
        return Intention(
            kind="task",
            task_goal="recommend_queue",
            reply="Reviewing the complete queue.",
            language="ro",
            action=None,
            data=IntentionData(**dict.fromkeys(IntentionData.model_fields)),
            evidence=[],
        ), {"provider": "simulated-intent-provider", "model": "synthetic-intent-model", "tools_enabled": False}


def run_task(env, tmp_path, provider=None, request=None):
    store = TaskStore(tmp_path / "recommendations.sqlite3")
    task = asyncio.run(
        recommend_queue(
            env["service"],
            store,
            env["dispatcher"],
            request or TaskRequest(goal="recommend_queue"),
            provider=provider or SimulatedDecisionProvider(),
        )
    )
    return task, store


def test_full_25_and_model_choices_preserve_original_ml_evidence(env, tmp_path):
    context = authorized_snapshot(env["service"], env["dispatcher"], "demo-vara")
    baseline = analyze_queue(context)
    assert len(context["work_items"]) >= 600 and baseline["total"] == 25
    provider = SimulatedDecisionProvider()
    task, store = run_task(env, tmp_path, provider)
    assert task.status == "completed", task.error
    result = task.result
    assert result["complete"] and result["total"] == 25
    assert result["expected_ids"] == result["analyzed_ids"] == baseline["expected_ids"]
    assert result["decision_source"] == "llm"
    assert result["provider"]["provider"] == "simulated-decision-provider"
    payload = json.loads(provider.prompts[0].split("\nINPUT JSON:\n")[1])
    assert len(payload["review_queue"]) == 25
    assert "routes" not in payload["plan"]
    assert [r["source"] for r in payload["review_queue"]] == [r["evidence"]["source"] for r in baseline["items"]]
    for before, after in zip(baseline["items"], result["items"], strict=True):
        for field in ("evidence", "assessment", "decision", "reason"):
            assert after[field] == before[field]
        assert after["checked_evidence"] and after["evidence_values_checked"]
        assert after["suggested_decision"] == ("defer" if after["assessment"]["status"] == "available" else None)
    second, _ = run_task(env, tmp_path / "contrast", SimulatedDecisionProvider("reject"))
    assert any(
        a["suggested_decision"] != b["suggested_decision"]
        for a, b in zip(result["items"], second.result["items"], strict=True)
    )
    assert TaskStore(store.path).get(env["dispatcher"], task.task_id) == task
    assert env["service"].context(env["dispatcher"])["plan"]["version"] == task.plan_version


def mutate_output(kind):
    def mutate(rows, _):
        if kind == "missing":
            rows.pop()
        elif kind == "duplicate":
            rows[-1] = deepcopy(rows[0])
        elif kind == "unknown":
            rows[-1]["work_item_id"] = "unknown-synthetic-id"
        elif kind == "false_evidence":
            rows[0]["evidence"][0]["value_json"] = '"fabricated"'
        elif kind == "other_item":
            rows[0]["evidence"] = rows[1]["evidence"]
        elif kind == "id_only":
            path = rows[0]["evidence"][0]["path"].split("/assessment/")[0]
            rows[0]["evidence"] = [{"path": path + "/work_item_id", "value_json": json.dumps(rows[0]["work_item_id"])}]
        elif kind == "hallucinated_metric":
            rows[0]["agent_reason"] = "This will save 987654321 lei."
        elif kind == "effect":
            rows[0]["agent_reason"] = "I have dispatched the team."
        elif kind == "passive_effect":
            rows[0]["agent_reason"] = "The case was repaired."

    return mutate


@pytest.mark.parametrize(
    "kind",
    [
        "missing",
        "duplicate",
        "unknown",
        "false_evidence",
        "other_item",
        "id_only",
        "hallucinated_metric",
        "effect",
        "passive_effect",
    ],
)
def test_invalid_output_fails_durably_without_preparing(env, tmp_path, monkeypatch, kind):
    monkeypatch.setattr(env["service"], "prepare", lambda *a, **k: pytest.fail("LLM must never prepare"))
    task, store = run_task(env, tmp_path, SimulatedDecisionProvider(mutation=mutate_output(kind)))
    assert task.status == "failed" and not task.result and not task.proposal
    assert TaskStore(store.path).get(env["dispatcher"], task.task_id) == task


def test_invalid_assessments_and_capacity_approval_abstain(env, tmp_path):
    def force_approve(rows, payload):
        for row in rows:
            row["suggested_decision"] = "approve"

    task, _ = run_task(env, tmp_path, SimulatedDecisionProvider(mutation=force_approve))
    assert task.status == "completed"
    for row in task.result["items"]:
        blocked = row["assessment"]["status"] != "available" or row["decision"]["rule_id"] == "R-B-REGION-CAP"
        assert row["suggested_decision"] == (None if blocked else "approve")
        assert row["recommendation"] == ("abstain" if blocked else "approve")
        assert "invalid_assessment" not in row["agent_reason"]
    assert {r["constraint"] for r in task.result["items"]} >= {"invalid_assessment", "capacity_constraint"}


@pytest.mark.parametrize("mode", ["error", "missing", "timeout", "metadata"])
def test_provider_unavailable_or_invalid_never_fabricates_success(env, tmp_path, monkeypatch, mode):
    import cyberpunks.agentic.llm_decisions as module

    class BrokenProvider:
        async def structured(self, prompt, schema):
            if mode == "timeout":
                await asyncio.Event().wait()
            if mode == "metadata":
                output, _ = await SimulatedDecisionProvider().structured(prompt, schema)
                return output, {}
            raise ChannelError("provider_auth_missing", "Synthetic unavailable provider")

    monkeypatch.setattr(module, "INFERENCE_SECONDS", 0.01 if mode == "timeout" else 85)
    task, store = run_task(env, tmp_path, object() if mode == "missing" else BrokenProvider())
    assert task.status == "failed" and task.error
    assert TaskStore(store.path).get(env["dispatcher"], task.task_id) == task


@pytest.mark.parametrize("change", ["version", "same_version_source", "identity", "authorization"])
def test_reread_version_context_identity_before_publication(env, tmp_path, monkeypatch, change):
    service, actor = env["service"], env["dispatcher"]
    original = service.context

    async def changed():
        if change == "identity":
            actor.permissions.append("synthetic-membership-change")
        elif change == "authorization":
            monkeypatch.setattr(service, "context", lambda *a, **k: (_ for _ in ()).throw(PermissionError()))
        else:

            def fresh(*args, **kwargs):
                context = deepcopy(original(*args, **kwargs))
                if change == "version":
                    context["plan"]["version"] = "changed"
                else:
                    context["work_items"][0]["asset_id"] = "changed-source-same-version"
                return context

            monkeypatch.setattr(service, "context", fresh)

    task, _ = run_task(env, tmp_path, SimulatedDecisionProvider(callback=changed))
    assert task.status == "failed" and not task.result


def test_one_live_lease_then_recovery_uses_saved_task(env, tmp_path):
    store = TaskStore(tmp_path / "tasks.sqlite3")
    request = TaskRequest(goal="recommend_queue", request_key="synthetic-event")
    actor, service = env["dispatcher"], env["service"]
    task = store.create(actor, request, service.context(actor)["plan"]["version"])
    old = store.claim(actor, task.task_id, seconds=LEASE_SECONDS)
    provider = SimulatedDecisionProvider()
    running = asyncio.run(recommend_queue(service, store, actor, request, provider=provider, task_id=task.task_id))
    assert running.status == "running" and not provider.prompts
    with sqlite3.connect(store.path) as db:
        db.execute("UPDATE agent_tasks SET lease_until=0 WHERE id=?", (task.task_id,))
    recovered = asyncio.run(
        recommend_queue(service, TaskStore(store.path), actor, request, provider=provider, task_id=task.task_id)
    )
    assert recovered.task_id == task.task_id and recovered.status == "completed"
    assert len(provider.prompts) == 1 and len(store.list(actor, "demo-vara")) == 1
    with pytest.raises(ValueError):
        store.update(actor, task.task_id, claim_token=old, status="failed")


def task_client(env, store, provider):
    app = FastAPI()
    app.include_router(create_router(env["service"], store, provider=provider))
    return TestClient(app)


def test_authenticated_prepare_saved_choice_idempotent_then_confirm_real_planner(env, tmp_path):
    task, store = run_task(env, tmp_path)
    parent = task.model_dump()
    client = task_client(env, store, SimulatedDecisionProvider())
    headers = env["headers"](env["dispatcher"])
    actionable = [r for r in task.result["items"] if r["suggested_decision"]]
    row = actionable[0]
    url = f"/api/conversation/tasks/{task.task_id}/recommendations/{row['work_item_id']}/prepare"
    assert client.post(url + "?scenario=another-scenario", headers=headers, json={}).status_code == 404
    assert client.post(url, json={}).status_code == 401
    assert client.post(url, headers=env["headers"](env["customer"]), json={}).status_code == 404
    assert client.post(url, headers=headers, json={"decision": "approve"}).status_code == 422
    first = client.post(url, headers=headers, json={})
    assert first.status_code == 200, first.text
    child = first.json()
    assert child["goal"] == "prepare_operation" and child["status"] == "awaiting_confirmation"
    assert child["task_id"] != task.task_id
    data = child["proposal"]["data"]
    assert data["decision"] == row["suggested_decision"] and data["note"] == row["agent_reason"]
    assert data["work_item_id"] == row["work_item_id"] and data["plan_version"] == task.plan_version
    assert client.post(url, headers=headers, json={}).json() == child
    assert store.get(env["dispatcher"], task.task_id).model_dump() == parent
    confirmed = env["client"].post(
        f"/api/operations/proposals/{child['proposal']['proposal_id']}/confirm",
        headers=headers,
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["status"] == "succeeded"
    assert env["service"].context(env["dispatcher"])["plan"]["version"] != task.plan_version
    second_url = f"/api/conversation/tasks/{task.task_id}/recommendations/{actionable[1]['work_item_id']}/prepare"
    assert client.post(second_url, headers=headers, json={}).status_code == 409
    assert client.post(url, headers=headers, json={}).status_code == 409
    assert store.get(env["dispatcher"], task.task_id).model_dump() == parent


def test_prepare_rejects_wrong_goal_abstention_permission_and_unknown(env, tmp_path):
    task, store = run_task(env, tmp_path)
    actor = env["dispatcher"]
    for wid in ("unknown", next(r["work_item_id"] for r in task.result["items"] if r["suggested_decision"] is None)):
        with pytest.raises(ValueError):
            prepare_recommendation(env["service"], store, actor, task.task_id, wid)
    with pytest.raises(PermissionError):
        prepare_recommendation(env["service"], store, actor.model_copy(update={"permissions": []}), task.task_id, "x")
    from cyberpunks.agentic.coordinator import AgenticCoordinator

    factual = AgenticCoordinator(env["service"], store).run(actor, TaskRequest(goal="analyze_queue"))
    with pytest.raises(ValueError):
        prepare_recommendation(
            env["service"], store, actor, factual.task_id, factual.result["items"][0]["work_item_id"]
        )


def test_prepare_never_rebases_between_parent_read_and_coordinator(env, tmp_path, monkeypatch):
    task, store = run_task(env, tmp_path)
    service, actor = env["service"], env["dispatcher"]
    original = service.context
    calls = 0

    def racing(*args, **kwargs):
        nonlocal calls
        calls += 1
        context = deepcopy(original(*args, **kwargs))
        if calls >= 2:
            context["plan"]["version"] = "synthetic-concurrent-plan"
        return context

    monkeypatch.setattr(service, "context", racing)
    monkeypatch.setattr(
        service, "prepare", lambda *a, **k: pytest.fail("Must reject original version before preparation")
    )
    row = next(r for r in task.result["items"] if r["suggested_decision"])
    with pytest.raises(ValueError):
        prepare_recommendation(service, store, actor, task.task_id, row["work_item_id"])
    children = [t for t in store.list(actor, "demo-vara") if t.task_id != task.task_id]
    assert len(children) == 1 and children[0].status == "failed"


def test_router_creates_and_resumes_same_queue_task(env, tmp_path):
    store = TaskStore(tmp_path / "router.sqlite3")
    provider = SimulatedDecisionProvider()
    client = task_client(env, store, provider)
    headers = env["headers"](env["dispatcher"])
    request = TaskRequest(goal="recommend_queue", request_key="one-request")
    response = client.post("/api/conversation/tasks", headers=headers, json=request.model_dump())
    assert response.status_code == 200 and response.json()["status"] == "completed"
    task = response.json()
    assert client.post(f"/api/conversation/tasks/{task['task_id']}/resume", headers=headers).json() == task
    assert client.post("/api/conversation/tasks", headers=headers, json=request.model_dump()).json() == task
    assert len(provider.prompts) == 1
    queued_request = TaskRequest(goal="recommend_queue", request_key="queued-for-restart")
    queued = store.create(env["dispatcher"], queued_request, task["plan_version"])
    resumed = client.post(f"/api/conversation/tasks/{queued.task_id}/resume", headers=headers)
    assert resumed.status_code == 200 and resumed.json()["status"] == "completed"
    assert resumed.json()["task_id"] == queued.task_id


def test_conversation_classifies_queue_and_retry_skips_provider(env):
    provider = SimulatedDecisionProvider()
    service = ConversationService(env["service"], provider)
    request = ChatRequest(message="ce ai face cu cele25 tichete")
    first = asyncio.run(service.chat(env["dispatcher"], request, event_key="synthetic-whatsapp-event"))
    second = asyncio.run(service.chat(env["dispatcher"], request, event_key="synthetic-whatsapp-event"))
    assert first == second and first["task"]["status"] == "completed"
    assert len(provider.turns) == len(provider.prompts) == 1
    assert first["provider"] == "simulated-decision-provider"
    payload = json.loads(provider.prompts[0].split("\nINPUT JSON:\n")[1])
    assert payload["user_preference"] == request.message
    assert len(payload["review_queue"]) == 25
    assert "recommend_queue" in SYSTEM
    assert not first["provenance"]["write_executed"]


@pytest.mark.parametrize(
    "message",
    [
        "Nu recomanda decizii pentru toate tichetele.",
        'Explică expresia "ce ai face cu cele25 tichete".',
        "Recomandă cum să șterg toate tichetele.",
        "Dacă te-aș întreba ce ai face cu toate tichetele, ce înseamnă asta?",
    ],
)
def test_negative_quoted_hypothetical_and_deletion_requests_always_use_classifier(env, message):
    class Classifier(SimulatedDecisionProvider):
        async def turn(self, prompt):
            self.turns.append(prompt)
            return Intention(
                kind="clarify",
                task_goal=None,
                language="ro",
                reply="Pot pregăti o revizuire pentru confirmare.",
                action=None,
                data=IntentionData(**dict.fromkeys(IntentionData.model_fields)),
                evidence=[],
            ), {"provider": "simulated-intent-provider", "model": "synthetic"}

    provider = Classifier()
    result = asyncio.run(
        ConversationService(env["service"], provider).chat(env["dispatcher"], ChatRequest(message=message))
    )
    assert len(provider.turns) == 1 and not provider.prompts
    assert "task" not in result and result["proposal"] is None


def test_selected_valid_recommendation_prepares_with_own_evidence_and_reason(env):
    context = env["service"].context(env["dispatcher"])
    _index, item = next(
        (i, w)
        for i, w in enumerate(context["work_items"])
        if w["decision"]["decision"] == "human_review" and w["assessment"]["status"] == "available"
    )

    class SelectedProvider:
        async def turn(self, prompt):
            payload = json.loads(prompt.split("\nINPUT JSON:\n")[1])
            selected = payload["scoped_context"]["work_items"]
            projected_index = next(i for i, w in enumerate(selected) if w["work_item_id"] == item["work_item_id"])
            data = dict.fromkeys(IntentionData.model_fields)
            data.update(
                work_item_id=item["work_item_id"], decision="defer", note="Capacity requires dispatcher review."
            )
            return Intention(
                kind="prepare",
                language="en",
                reply="I recommend deferring for capacity review.",
                action="review_work_item",
                data=data,
                evidence=[{"path": f"/work_items/{projected_index}/assessment/status", "value_json": '"available"'}],
            ), {"provider": "simulated", "model": "synthetic"}

    result = asyncio.run(
        ConversationService(env["service"], SelectedProvider()).chat(
            env["dispatcher"],
            ChatRequest(
                message="What would you recommend for this case?", selection={"work_item_id": item["work_item_id"]}
            ),
        )
    )
    assert result["proposal"]["action"] == "review_work_item"
    assert result["proposal"]["data"]["decision"] == "defer"
    assert result["proposal"]["data"]["note"] == "Capacity requires dispatcher review."
    assert result["provenance"]["evidence_values_checked"]


def test_reusable_real_provider_protocol_supports_queue_schema():
    from cyberpunks.channels.codex import parse_events

    raw = b"\n".join(
        json.dumps(event).encode()
        for event in [
            {"type": "item.completed", "item": {"type": "agent_message", "text": '{"items": []}'}},
            {"type": "turn.completed", "usage": {"input_tokens": 7}},
        ]
    )
    output, usage = parse_events(raw, QueueDecisions)
    assert output == QueueDecisions(items=[]) and usage == {"input_tokens": 7}


def test_safety_constraint_and_exact_percentages_use_real_source(env):
    context = authorized_snapshot(env["service"], env["dispatcher"], "demo-vara")
    baseline = analyze_queue(context)
    rows = []
    for item in baseline["items"]:
        rows.append(
            {
                "work_item_id": item["work_item_id"],
                "suggested_decision": "reject",
                "agent_reason": "Dispatcher assessment is required.",
                "evidence": [
                    {
                        "path": item["evidence"]["path"] + "/assessment/status",
                        "value_json": json.dumps(item["assessment"]["status"]),
                    }
                ],
            }
        )
    available = next(
        row
        for row in rows
        if next(item for item in baseline["items"] if item["work_item_id"] == row["work_item_id"])["assessment"][
            "status"
        ]
        == "available"
    )
    index = next(i for i, w in enumerate(context["work_items"]) if w["work_item_id"] == available["work_item_id"])
    # Explicit test-only source perturbation on the complete isolated snapshot.
    context["work_items"][index]["impact"]["safety_flag"] = True
    output = QueueDecisions.model_validate({"items": rows})
    result = validate_decisions(context, output, {"provider": "simulated", "model": "synthetic"})
    safety = next(row for row in result["items"] if row["work_item_id"] == available["work_item_id"])
    assert safety["suggested_decision"] is None and safety["constraint"] == "safety_constraint"
    context["work_items"][index]["impact"]["safety_flag"] = False
    from decimal import Decimal

    score = context["work_items"][index]["assessment"]["score"]
    available["agent_reason"] = f"The exact model score is {Decimal(str(score)) * 100}%."
    available["evidence"].append({"path": f"/work_items/{index}/assessment/score", "value_json": json.dumps(score)})
    validate_decisions(context, {"items": rows}, {"provider": "simulated", "model": "synthetic"})


@pytest.mark.parametrize("endpoint", ["create", "resume"])
def test_tasks_share_chat_limiter_and_return_429(env, tmp_path, monkeypatch, endpoint):
    import cyberpunks.agentic.router as module
    from cyberpunks.channels.limits import Limits

    limiter = Limits(per_minute=100)
    monkeypatch.setattr(module, "limits", limiter)
    actor = env["dispatcher"]
    store = TaskStore(tmp_path / "limited.sqlite3")
    provider = SimulatedDecisionProvider()
    client = task_client(env, store, provider)
    request = TaskRequest(goal="recommend_queue", request_key="limited-request")
    if endpoint == "resume":
        task = store.create(actor, request, env["service"].context(actor)["plan"]["version"])
        url = f"/api/conversation/tasks/{task.task_id}/resume"
    else:
        url = "/api/conversation/tasks"

    async def held():
        async with limiter.acquire((actor.organization_id, actor.user_id)):
            response = client.post(
                url, headers=env["headers"](actor), json=request.model_dump() if endpoint == "create" else None
            )
            assert response.status_code == 429, response.text
            assert response.headers["Retry-After"] == "60"

    asyncio.run(held())
    assert not provider.prompts


@pytest.mark.parametrize("choice", [None, "approve"])
def test_unavailable_prediction_can_explain_abstention_but_cannot_justify_an_action(env, tmp_path, choice):
    def explain(rows, payload):
        for row, item in zip(rows, payload["review_queue"], strict=True):
            source = item["source"]
            if source["assessment"]["status"] == "available":
                continue
            row["suggested_decision"] = choice
            row["agent_reason"] = "The recorded model output is unusable because the source assessment needs more data."
            row["evidence"].append(
                {
                    "path": item["source_path"] + "/prediction/score",
                    "value_json": json.dumps(source["prediction"]["score"]),
                }
            )

    task, store = run_task(env, tmp_path, SimulatedDecisionProvider(mutation=explain))
    if choice is None:
        assert task.status == "completed", task.error
        invalid = next(r for r in task.result["items"] if r["assessment"]["status"] != "available")
        assert invalid["suggested_decision"] is None and invalid["constraint"] == "invalid_assessment"
        with pytest.raises(ValueError, match="No actionable"):
            prepare_recommendation(env["service"], store, env["dispatcher"], task.task_id, invalid["work_item_id"])
    else:
        assert task.status == "failed" and task.error == "assessment_unavailable"
