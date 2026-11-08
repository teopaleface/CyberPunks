from types import SimpleNamespace

import pytest

from cyberpunks.agentic.contracts import TaskRequest
from cyberpunks.agentic.effects import observe_effect, prepare_operation


def test_passive_missing_does_not_reconcile():
    ops = SimpleNamespace(context=lambda *a: {}, command=lambda *a: pytest.fail("reconciliation"))
    with pytest.raises(NotImplementedError):
        observe_effect(ops, None, "proposal", "demo-vara")


def test_prepare_checks_version():
    ops = SimpleNamespace(context=lambda *a: {"plan_version": "new"}, prepare=lambda *a: pytest.fail("stale"))
    with pytest.raises(ValueError):
        prepare_operation(
            ops, None, TaskRequest(goal="prepare_operation", action="approve_plan"), {"plan_version": "old"}
        )


def test_real_prepare_snapshot_versions_and_retry(env):
    ops = env["service"]
    actor = env["customer"]
    created = ops.prepare(
        actor,
        "create_case",
        {
            "connection_id": env["binding"]["connection_id"],
            "symptom": "Inverter stops at noon",
            "symptom_type": "meter",
        },
        "demo-vara",
    )
    case = ops.confirm(actor, created["proposal_id"])["result"]["case"]
    actor = env["customer"]
    ops = env["service"]
    context = ops.context(actor, "demo-vara")
    request = TaskRequest(
        goal="prepare_operation",
        action="request_human",
        case_id=case["case_id"],
        request_key="real-retry",
        data={"reason": "Human review requested"},
    )
    proposal = prepare_operation(ops, actor, request, context)
    assert proposal["data"]["plan_version"] == context["plan"]["version"]
    assert proposal["data"]["case_version"] == case["version"]
    assert prepare_operation(ops, actor, request, context)["proposal_id"] == proposal["proposal_id"]
    stale = {**context, "plan": {**context["plan"], "version": "stale"}}
    with pytest.raises(ValueError):
        prepare_operation(ops, actor, request, stale)
