"""Synthetic LLM responses, real operations on the coordinator's full fresh copy."""

import asyncio
import json
import os
import shutil
from copy import deepcopy
from pathlib import Path

import pytest

from cyberpunks.agentic.queue_analysis import analyze_queue
from cyberpunks.agentic.snapshots import authorized_snapshot
from cyberpunks.channels.voice_dispatch import run_dispatch
from cyberpunks.operations.models import Actor
from cyberpunks.operations.service import OperationsService


@pytest.fixture
def dispatch_env(tmp_path, full_run):
    source = Path(os.environ.get("DAYBREAK_OPERATIONS_TEST_DATA", full_run))
    assert (source / "plans/demo-vara/inputs").is_dir()
    target = tmp_path / "synthetic-full-copy"
    shutil.copytree(source, target)
    operations = OperationsService(target, tmp_path / "synthetic.sqlite3")
    bindings = operations.demo_bindings()
    actor = Actor(
        user_id="synthetic-voice-dispatcher",
        role="dispatcher",
        organization_id=bindings["organization_id"],
        permissions=bindings["permissions"],
    )
    return operations, actor


class SyntheticProvider:
    def __init__(self, choice="defer"):
        self.calls = []
        self.choice = choice

    async def structured(self, prompt, schema):
        payload = json.loads(prompt.split("\nINPUT JSON:\n")[1])
        self.calls.append(payload)
        return schema.model_validate(
            {
                "items": [
                    {
                        "work_item_id": item["work_item_id"],
                        "suggested_decision": self.choice,
                        "agent_reason": "Este necesară evaluarea dispecerului.",
                        "evidence": [
                            {
                                "path": item["source_path"] + "/assessment/status",
                                "value_json": json.dumps(item["source"]["assessment"]["status"]),
                            },
                            {
                                "path": item["source_path"] + "/decision/rule_id",
                                "value_json": json.dumps(item["source"]["decision"]["rule_id"]),
                            },
                        ],
                    }
                    for item in payload["review_queue"]
                ]
            }
        ), {"provider": "synthetic-dispatch-test", "model": "synthetic-test-model"}


def run(env, provider, **kw):
    return asyncio.run(
        run_dispatch(
            *env,
            event_key="synthetic-voice-event",
            authorize_actor=kw.pop("authorize_actor", lambda actor: actor),
            provider=provider,
            **kw,
        )
    )


def counts(operations):
    with operations.db.connect() as db:
        return tuple(
            db.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
            for t in ("commands", "manual_corrections", "proposals")
        )


def test_full_queue_automatic_serial_replan_and_restart(dispatch_env):
    operations, actor = dispatch_env
    before = authorized_snapshot(operations, actor, "demo-vara")
    baseline = analyze_queue(before)
    assert len(before["work_items"]) >= 600
    provider = SyntheticProvider()
    progress = []
    result = run(dispatch_env, provider, progress=progress.append)
    assert result["status"] == "completed"
    assert len(provider.calls) == 1
    assert len(provider.calls[0]["review_queue"]) == baseline["total"]
    assert result["applied"] >= 2, result
    assert len(result["items"]) == baseline["total"]
    assert counts(operations) == (result["applied"],) * 3
    assert result["provenance"]["write_executed"]
    assert progress[0]["status"] == "recommending" and progress[-1] == result
    for old, new in zip(baseline["items"], result["recommendations"]["items"], strict=True):
        assert old["evidence"] == new["evidence"]
        assert old["assessment"] == new["assessment"]
        assert old["decision"] == new["decision"]
    applied = [i for i in result["items"] if i["status"] == "applied"]
    assert len({i["request_data"]["plan_version"] for i in applied}) == len(applied)
    after = authorized_snapshot(operations, actor, "demo-vara")
    assert before["plan_version"] != after["plan_version"]
    assert {w["work_item_id"]: w.get("prediction") for w in before["work_items"]} == {
        w["work_item_id"]: w.get("prediction") for w in after["work_items"]
    }
    replay = run((OperationsService(operations.outputs, operations.db_path), actor), provider)
    assert len(provider.calls) == 1
    assert replay["applied"] == result["applied"]
    assert [i["command"]["command_id"] for i in replay["items"] if i["status"] == "applied"] == [
        i["command"]["command_id"] for i in applied
    ]
    assert counts(operations) == (result["applied"],) * 3
    assert "reparat" not in result["reply"] and "rezolvat" not in result["reply"]
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("choice,constraint", [("approve", "capacity_constraint"), ("defer", "safety_constraint")])
def test_abstentions_preserve_constraints(dispatch_env, choice, constraint):
    result = run(dispatch_env, SyntheticProvider(choice))
    for row in result["recommendations"]["items"]:
        item = next(i for i in result["items"] if i["work_item_id"] == row["work_item_id"])
        if row.get("constraint"):
            assert item["status"] == "abstained"
    assert any(i["constraint"] == "invalid_assessment" for i in result["items"] if i["status"] == "abstained")
    # The current live-data reference may have no valid safety assessment.
    blocked = [r for r in result["recommendations"]["items"] if r["constraint"] == constraint]
    assert all(r["suggested_decision"] is None for r in blocked)


def test_reauthorize_before_each_confirm_and_stop_on_revocation(dispatch_env, monkeypatch):
    operations, actor = dispatch_env
    original = operations.confirm
    revoked = False

    def confirm(*args):
        nonlocal revoked
        command = original(*args)
        revoked = True
        return command

    def authorize(current):
        assert current == actor
        if revoked:
            raise PermissionError("Synthetic authorization revoked")
        return current

    monkeypatch.setattr(operations, "confirm", confirm)
    with pytest.raises(PermissionError):
        run(dispatch_env, SyntheticProvider(), authorize_actor=authorize)
    assert counts(operations)[0] == 1


def test_changed_prediction_before_confirm_is_skipped(dispatch_env, monkeypatch):
    operations, _ = dispatch_env
    original = operations.context
    prepared = False
    prepare = operations.prepare

    def altered_context(*args):
        context = original(*args)
        if prepared:
            context = deepcopy(context)
            for item in context["work_items"]:
                item.setdefault("prediction", {})["confidence"] = "synthetic-changed-evidence"
        return context

    def mark_prepared(*args):
        nonlocal prepared
        proposal = prepare(*args)
        prepared = True
        return proposal

    monkeypatch.setattr(operations, "prepare", mark_prepared)
    monkeypatch.setattr(operations, "context", altered_context)
    result = run(dispatch_env, SyntheticProvider())
    assert result["applied"] == 0
    assert any(i["status"] == "skipped_changed" for i in result["items"])
    assert counts(operations)[0] == 0


def test_unknown_command_stops_serial_execution_without_claiming_success(dispatch_env, monkeypatch):
    operations, _ = dispatch_env
    observe = operations.observe_effect

    def uncertain(*args):
        saved = observe(*args)
        if saved.get("command"):
            saved["status"] = saved["command"]["status"] = "reconciling"
        return saved

    monkeypatch.setattr(operations, "observe_effect", uncertain)
    provider = SyntheticProvider()
    result = run(dispatch_env, provider)
    assert result["status"] == "needs_reconciliation"
    assert result["applied"] == 0
    assert counts(operations)[0] == 1
    again = run(dispatch_env, provider)
    assert again["status"] == "needs_reconciliation"
    assert counts(operations)[0] == 1 and len(provider.calls) == 1


def test_unauthorized_actor_never_calls_model(dispatch_env):
    operations, actor = dispatch_env
    provider = SyntheticProvider()
    with pytest.raises(PermissionError):
        run((operations, actor.model_copy(update={"role": "customer"})), provider)
    assert not provider.calls and counts(operations)[0] == 0


def test_lost_confirm_response_resumes_same_persisted_command(dispatch_env, monkeypatch):
    operations, _ = dispatch_env
    confirm = operations.confirm
    interrupted = False

    def lost_response(*args):
        nonlocal interrupted
        result = confirm(*args)
        if not interrupted:
            interrupted = True
            raise RuntimeError("Synthetic process failure after durable commit")
        return result

    monkeypatch.setattr(operations, "confirm", lost_response)
    provider = SyntheticProvider()
    with pytest.raises(RuntimeError):
        run(dispatch_env, provider)
    assert counts(operations)[0] == 1
    with operations.db.connect() as db:
        first_id = db.execute("SELECT command_id FROM commands").fetchone()[0]
    result = run(dispatch_env, provider)
    assert result["status"] == "completed" and len(provider.calls) == 1
    ids = [i["command"]["command_id"] for i in result["items"] if i["status"] == "applied"]
    assert ids.count(first_id) == 1
    assert counts(operations) == (result["applied"],) * 3


def test_invalid_llm_output_never_applies_and_replay_does_not_reinfer(dispatch_env):
    class InvalidProvider(SyntheticProvider):
        async def structured(self, prompt, schema):
            output, meta = await super().structured(prompt, schema)
            output.items = []
            return output, meta

    provider = InvalidProvider()
    first = run(dispatch_env, provider)
    again = run(dispatch_env, provider)
    assert first["status"] == again["status"] == "failed"
    assert counts(dispatch_env[0]) == (0, 0, 0)
    assert len(provider.calls) == 1


def test_evidence_rebinds_by_item_id_and_missing_plan_evidence_abstains(dispatch_env):
    from cyberpunks.channels.voice_dispatch import _unchanged

    operations, actor = dispatch_env
    context = authorized_snapshot(operations, actor, "demo-vara")
    row = next(
        r
        for r in analyze_queue(context)["items"]
        if r["assessment"]["status"] == "available" and not r["evidence"]["source"]["impact"].get("safety_flag")
    )
    row.update(
        suggested_decision="defer",
        evidence_values_checked=True,
        checked_evidence=[
            {"path": row["evidence"]["path"] + "/assessment", "value": row["assessment"]},
            {"path": "/plan/summary", "value": context["plan"]["summary"]},
        ],
    )
    reordered = deepcopy(context)
    reordered["work_items"].reverse()
    assert _unchanged(reordered, row)
    reordered["plan"].pop("summary")
    assert not _unchanged(reordered, row)
