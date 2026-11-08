"""Execute the private, explicitly authorized synthetic voice dispatcher workflow.

The caller owns intent recognition, the private demo allowlist and durable jobs.
``authorize_actor(actor)`` must freshly check that authority, raising on failure;
validators may return None/True or the unchanged Actor. It may be async.
``progress(state)`` may also be async. No messages or external services are used.
"""

from __future__ import annotations

import asyncio
import hashlib
import inspect
import json
from copy import deepcopy
from pathlib import Path

from cyberpunks.agentic.contracts import TaskRequest
from cyberpunks.agentic.llm_decisions import recommend_queue, valid_assessment
from cyberpunks.agentic.snapshots import authorized_snapshot
from cyberpunks.agentic.task_store import TaskStore
from cyberpunks.channels.conversation import pointer_value
from cyberpunks.channels.models import ChannelError
from cyberpunks.operations.models import OperationError

SCENARIO = "demo-vara"
ACTION = "review_work_item"


def _key(event_key, wid=None):
    # Length prefixes avoid collisions between arbitrary event and item strings.
    value = json.dumps([event_key, wid], ensure_ascii=False, separators=(",", ":"))
    return "voice-dispatch:" + hashlib.sha256(value.encode()).hexdigest()


async def _authorize(callback, actor):
    result = callback(actor)
    if inspect.isawaitable(result):
        result = await result
    if result is not None and result is not True and result != actor:
        raise PermissionError("Voice dispatcher authorization changed")
    if actor.role != "dispatcher" or ACTION not in actor.permissions:
        raise PermissionError("Dispatcher review permission required")


def _semantic(item):
    item = deepcopy(item)
    item.pop("version", None)
    # Every serial replan regenerates this audit pointer, even for unchanged
    # decisions. Its actual value is still checked if the LLM cited it.
    if isinstance(item.get("decision"), dict):
        item["decision"].pop("audit_id", None)
    return item


def _unchanged(context, row):
    matches = [(i, w) for i, w in enumerate(context["work_items"]) if w["work_item_id"] == row["work_item_id"]]
    if len(matches) != 1:
        return False
    index, current = matches[0]
    original = row["evidence"]["source"]
    if (
        (current.get("decision") or {}).get("decision") != "human_review"
        or not valid_assessment(context, current)
        or _semantic(current) != _semantic(original)
    ):
        return False
    choice = row.get("suggested_decision")
    rule = (current.get("decision") or {}).get("rule_id", "")
    if choice == "approve" and rule == "R-B-REGION-CAP":
        return False
    if choice in {"reject", "defer"} and ((current.get("impact") or {}).get("safety_flag") or "SAFETY" in rule):
        return False
    old_path = row["evidence"]["path"]
    for evidence in row.get("checked_evidence", []):
        path = evidence["path"]
        if path == old_path or path.startswith(old_path + "/"):
            path = f"/work_items/{index}" + path[len(old_path) :]
        try:
            actual = pointer_value(context, path)
        except (ChannelError, ValueError, KeyError, IndexError, TypeError):
            return False
        # JSON comparison distinguishes true from 1 and preserves exact evidence.
        if json.dumps(actual, sort_keys=True) != json.dumps(evidence["value"], sort_keys=True):
            return False
    return bool(row.get("evidence_values_checked") and row.get("checked_evidence"))


def _verified(observation, proposal, wid, choice):
    command = observation.get("command") or {}
    correction = (command.get("result") or {}).get("manual_correction") or {}
    return (
        observation.get("status") == command.get("status") == "succeeded"
        and bool(command.get("command_id"))
        and command.get("proposal_id") == proposal["proposal_id"]
        and command.get("action") == ACTION
        and correction.get("work_item_id") == wid
        and correction.get("requested_decision") == choice
    )


async def _apply(operations, store, actor, row, event_key, authorize_actor):
    wid, choice = row["work_item_id"], row["suggested_decision"]
    await _authorize(authorize_actor, actor)
    context = authorized_snapshot(operations, actor, SCENARIO)
    request = TaskRequest(
        goal="prepare_operation",
        action=ACTION,
        work_item_id=wid,
        request_key=_key(event_key, wid),
        data={"decision": choice, "note": row["agent_reason"]},
    )
    task = store.create(actor, request, context["plan_version"])
    receipt = {"work_item_id": wid, "decision": choice, "task_id": task.task_id, **task.result}
    if task.status in {"failed", "cancelled"}:
        return receipt
    proposal = task.proposal
    if proposal:
        observed = operations.observe_effect(actor, proposal["proposal_id"], SCENARIO)
        if _verified(observed, proposal, wid, choice):
            receipt.update(status="applied", command=observed["command"], proposal_id=proposal["proposal_id"])
            if task.status != "completed":
                token = store.claim(actor, task.task_id, seconds=180)
                if token:
                    store.update(actor, task.task_id, claim_token=token, status="completed", result=receipt)
            return receipt
        if observed.get("command"):
            return {**receipt, "status": "needs_reconciliation", "command": observed["command"]}
        if task.status == "completed":
            return {**receipt, "status": "needs_reconciliation"}
    token = store.claim(actor, task.task_id, seconds=180)
    if token is None:
        return {**receipt, "status": "running"}

    def save(phase, **fields):
        nonlocal token, task, receipt
        receipt.update(fields)
        task = store.update(actor, task.task_id, claim_token=token, status=phase, result=receipt, proposal=proposal)
        token = None

    def reclaim():
        nonlocal token
        token = store.claim(actor, task.task_id, seconds=180)
        return token is not None

    try:
        if not _unchanged(context, row):
            save("cancelled", status="skipped_changed")
            return receipt
        data = receipt.get("request_data")
        if data is None:
            data = {
                "work_item_id": wid,
                "decision": choice,
                "note": row["agent_reason"],
                "plan_version": context["plan_version"],
                "idempotency_key": _key(event_key, wid),
            }
            # Persist the EXACT prepare payload before its first effect. Retrying
            # with a new plan version would conflict with a consumed key.
            save("running", request_data=data, status="running")
            if not reclaim():
                return receipt
        if proposal is None:
            proposal = operations.prepare(actor, ACTION, data, SCENARIO)
            save("running", proposal_id=proposal["proposal_id"], status="running")
            if not reclaim():
                return receipt
        if proposal.get("action") != ACTION or any(proposal.get("data", {}).get(k) != v for k, v in data.items()):
            raise ValueError("Unexpected persisted dispatcher proposal")
        await _authorize(authorize_actor, actor)
        fresh = authorized_snapshot(operations, actor, SCENARIO)
        if not _unchanged(fresh, row) or fresh["plan_version"] != proposal["plan_version"]:
            save("cancelled", status="skipped_changed")
            return receipt
        command = operations.confirm(actor, proposal["proposal_id"])
        observed = operations.observe_effect(actor, proposal["proposal_id"], SCENARIO)
        if (
            _verified(observed, proposal, wid, choice)
            and command.get("command_id") == observed["command"]["command_id"]
        ):
            save("completed", status="applied", command=observed["command"])
        else:
            save("needs_reconciliation", status="needs_reconciliation", command=observed.get("command") or command)
    except asyncio.CancelledError:
        if token:
            save("needs_reconciliation", status="needs_reconciliation")
        raise
    except (OperationError, ValueError) as exc:
        # Observe a possibly committed command before reporting any error.
        observed = operations.observe_effect(actor, proposal["proposal_id"], SCENARIO) if proposal else {}
        if proposal and _verified(observed, proposal, wid, choice):
            save("completed", status="applied", command=observed["command"])
        elif observed.get("command"):
            save("needs_reconciliation", status="needs_reconciliation", command=observed["command"])
        else:
            code = getattr(exc, "code", "dispatch_failed")
            if code == "reconciliation_pending":
                save("needs_reconciliation", status="needs_reconciliation", error=code)
            else:
                save(
                    "failed", status="skipped_changed" if code in {"stale_plan", "stale_case"} else "failed", error=code
                )
    return receipt


async def run_dispatch(operations, actor, *, event_key, authorize_actor, provider=None, progress=None) -> dict:
    """Recommend the FULL scoped queue once; apply validated reviews serially.

    A replay uses the immutable saved LLM result even after our own replans.
    Per-item durable tasks retain original prepare data, proposals and commands.
    Private-demo execution authority must be checked by the caller's callback.
    """
    if not isinstance(event_key, str) or not event_key.strip():
        raise ValueError("A stable server event key is required")
    await _authorize(authorize_actor, actor)
    context = authorized_snapshot(operations, actor, SCENARIO)
    store = TaskStore(Path(operations.db_path).with_name("agentic-tasks.sqlite3"))
    request = TaskRequest(goal="recommend_queue", request_key=_key(event_key))
    task = store.create(actor, request, context["plan_version"])

    async def notify(state):
        if progress:
            value = progress(deepcopy(state))
            if inspect.isawaitable(value):
                await value

    await notify({"status": "recommending", "task_id": task.task_id})
    if task.status in {"queued", "running"}:
        task = await recommend_queue(operations, store, actor, request, provider=provider, task_id=task.task_id)
    await _authorize(authorize_actor, actor)
    items = []
    if task.status == "completed" and task.result.get("decision_source") == "llm":
        for row in task.result["items"]:
            if row.get("suggested_decision") not in {"approve", "reject", "defer"} or row.get("constraint"):
                items.append(
                    {
                        "work_item_id": row["work_item_id"],
                        "status": "abstained",
                        "reason": row["agent_reason"],
                        "constraint": row.get("constraint"),
                    }
                )
            else:
                item = await _apply(operations, store, actor, row, event_key, authorize_actor)
                items.append(item)
                if item["status"] in {"running", "needs_reconciliation"}:
                    break  # Never advance the plan while a previous effect is unknown.
            await notify({"status": "applying", "task_id": task.task_id, "items": items})
    applied = sum(i["status"] == "applied" for i in items)
    pending = task.status in {"queued", "running"} or any(i["status"] == "running" for i in items)
    uncertain = any(i["status"] == "needs_reconciliation" for i in items)
    status = (
        "running"
        if pending
        else "needs_reconciliation"
        if uncertain
        else "completed"
        if task.status == "completed"
        else "failed"
    )
    remaining = max(0, task.result.get("total", 0) - applied)
    reply = (
        "Analiza cazurilor din demo este în curs."
        if pending
        else f"Am aplicat {applied} decizii în demo. Un rezultat cere verificare; m-am oprit."
        if uncertain
        else f"Am aplicat {applied} decizii în demo; {remaining} cazuri au rămas pentru evaluare."
        if status == "completed"
        else "Recomandările nu au putut fi verificate. Nu am aplicat decizii."
    )
    result = {
        "status": status,
        "error": task.error,
        "reply": reply,
        "task_id": task.task_id,
        "items": items,
        "applied": applied,
        "remaining": remaining,
        "recommendations": task.result,
        "provenance": {
            "synthetic": True,
            "scenario": SCENARIO,
            "event_key": event_key,
            "write_executed": applied > 0,
            "decision_source": "llm",
            "plan_version": task.plan_version,
            "provider": task.result.get("provider"),
        },
    }
    await notify(result)
    return result
