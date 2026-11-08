"""Presentation regressions on a complete reference copy; all effects are local/simulated."""

import os
import shutil
from pathlib import Path

import pytest

from cyberpunks.operations.models import OperationError

from .test_whatsapp_calls import demo_call  # noqa: F401


@pytest.fixture(scope="session")
def full_run(full_run, tmp_path_factory):
    source = Path(os.environ.get("DAYBREAK_OPERATIONS_TEST_DATA", full_run))
    assert (source / "plans/demo-vara/inputs").is_dir()
    target = tmp_path_factory.mktemp("presentation-complete-reference") / "data"
    shutil.copytree(source, target)
    return target


def test_cached_incident_proposal_is_not_replayed_after_plan_approval(demo_call, env, monkeypatch):  # noqa: F811
    from cyberpunks.channels import voice_briefs

    monkeypatch.setattr(voice_briefs, "answer_demo", demo_call["real_brief"])
    # No incident execution and no report sender: this request only prepares locally.
    message = "Sunt client. Raportez că mi-a căzut un stâlp de curent."
    body = {"caller_id": "+40700000000", "conversation_id": "synthetic-version-call", "message": message}
    client = demo_call["client"]
    first = client.post("/api/voice/turn", headers=demo_call["headers"], json=body)
    assert first.status_code == 200 and "pregătită pentru Confirm" in first.json()["reply"]
    customer = env["actors"]["customer"]
    proposal_id = env["operations"].context(customer)["pending_proposals"][0]["proposal_id"]
    dispatcher = env["actors"]["dispatcher"]
    plan = env["operations"].context(dispatcher)["plan"]
    before = plan["version"]
    approval = env["operations"].prepare(
        dispatcher, "approve_plan", {"plan_id": plan["plan_id"], "plan_version": before}
    )
    assert env["operations"].confirm(dispatcher, approval["proposal_id"])["status"] == "succeeded"
    assert env["operations"].context(dispatcher)["plan"]["version"] != before
    assert env["operations"].context(env["actors"]["customer"])["pending_proposals"] == []
    with pytest.raises(OperationError) as stale:
        env["operations"].confirm(customer, proposal_id)
    assert stale.value.code == "stale_plan"
    replay = client.post("/api/voice/turn", headers=demo_call["headers"], json=body)
    assert "pregătită pentru Confirm" not in replay.json().get("reply", ""), replay.json()
