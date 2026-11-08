"""Customer demo execution on complete copied data; every actor/event is synthetic."""

import os
import shutil
from pathlib import Path

import pytest

from cyberpunks.channels.voice_briefs import SAFETY, answer_demo
from cyberpunks.operations.models import Actor, OperationError
from cyberpunks.operations.service import OperationsService

POLE = "Raportez că mi-a picat stâlpul de curent."
OUTAGE = "Am rămas fără curent."


@pytest.fixture
def demo(tmp_path, full_run):
    source = Path(os.environ.get("DAYBREAK_OPERATIONS_TEST_DATA", full_run))
    assert (source / "plans/demo-vara/inputs").is_dir()
    target = tmp_path / "synthetic-complete-copy"
    shutil.copytree(source, target)
    service = OperationsService(target, tmp_path / "synthetic.sqlite3")
    binding = service.demo_bindings()
    base = {"organization_id": binding["organization_id"]}
    actors = {
        "customer": Actor(
            user_id="synthetic-client", role="customer", connection_ids=binding["connection_ids"], **base
        ),
        "dispatcher": Actor(
            user_id="synthetic-dispatch", role="dispatcher", permissions=binding["permissions"], **base
        ),
        "technician": Actor(user_id="synthetic-tech", role="technician", crew_id=binding["crew_id"], **base),
    }
    return service, actors, binding["connection_ids"][0]


def counts(service):
    with service.db.connect() as db:
        return tuple(
            db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in ("proposals", "commands", "events", "cases")
        )


def say(demo, message=POLE, role="customer", **kwargs):
    service, actors, connection = demo
    return answer_demo(
        service, actors[role], message, event_key="synthetic-stable-event", connection_id=connection, **kwargs
    )


@pytest.mark.parametrize("message,action", [(POLE, "request_human"), (OUTAGE, "create_case")])
def test_executes_persisted_customer_command_and_replay_is_identical(demo, message, action):
    service, actors, _ = demo
    version = service.context(actors["dispatcher"])["plan"]["version"]
    result = say(demo, message, execute_incident=True)
    command = result["command"]
    assert command["status"] == "succeeded" and command["action"] == action
    assert result["provenance"]["write_executed"] is True
    assert "Am înregistrat" in result["reply"] and "în demo" in result["reply"]
    saved = service.observe_effect(actors["customer"], result["proposal"]["proposal_id"], "demo-vara")
    assert saved["command"] == command
    if action == "request_human":
        human = command["result"]["human_request"]
        assert human["priority"] == "urgent" and human["status"] == "queued"
        assert human["external_contact"] is False and result["reply"].startswith(SAFETY)
    else:
        assert command["result"]["case"]["symptom_type"] == "outage"
        assert command["result"]["case"]["synthetic"] is True
    after = counts(service)
    assert after[:2] == (1, 1) and after[2] == 1
    assert after[3] == (1 if action == "create_case" else 0)
    again = say(demo, message, execute_incident=True)
    assert again["command"] == command and counts(service) == after
    assert service.context(actors["dispatcher"])["plan"]["version"] == version


@pytest.mark.parametrize("message", [POLE, OUTAGE])
def test_default_remains_prepare_only_and_can_then_execute_same_event(demo, message):
    result = say(demo, message)
    assert result["provenance"]["write_executed"] is False
    assert result["proposal"]["requires_confirmation"] is True
    assert counts(demo[0]) == (1, 0, 0, 0)
    applied = say(demo, message, execute_incident=True)
    assert applied["proposal"]["proposal_id"] == result["proposal"]["proposal_id"]
    assert applied["command"]["status"] == "succeeded"


@pytest.mark.parametrize(
    "message",
    [
        "da",
        "Da, confirm",
        "Nu mi-a picat stâlpul de curent.",
        "Nu am rămas fără curent.",
        'Clientul spune "mi-a picat stâlpul de curent".',
        "'Am rămas fără curent.'",
        "Dacă mi-a picat stâlpul de curent",
        "Poate am rămas fără curent.",
        "Raportez un incident de curent",
        "Mi-a picat curentul?",
        "Mi-a picat stâlpul de curent?",
        "Aș raporta că mi-a picat stâlpul de curent.",
        "N-a picat stâlpul de curent.",
        "Aprobă planul",
        "Revizuiește tichetul",
    ],
)
def test_unclear_negative_quoted_generic_and_other_actions_have_no_effect(demo, message):
    result = say(demo, message, execute_incident=True)
    assert result is None or result["proposal"] is None
    assert counts(demo[0]) == (0, 0, 0, 0)


@pytest.mark.parametrize("role", ["dispatcher", "technician"])
@pytest.mark.parametrize("message", [POLE, OUTAGE, "Da, confirm", "Aprobă planul"])
def test_other_roles_never_execute(demo, role, message):
    say(demo, message, role, execute_incident=True)
    assert counts(demo[0]) == (0, 0, 0, 0)


def test_missing_or_foreign_connection_cannot_execute(demo):
    service, actors, _ = demo
    for connection in (None, "synthetic-foreign"):
        result = answer_demo(
            service,
            actors["customer"],
            POLE,
            event_key="synthetic-event",
            connection_id=connection,
            execute_incident=True,
        )
        assert result["proposal"] is None and SAFETY in result["reply"]
    assert counts(service) == (0, 0, 0, 0)


def test_event_conflict_and_missing_event_never_duplicate(demo):
    say(demo, execute_incident=True)
    before = counts(demo[0])
    with pytest.raises(OperationError, match="idempotency"):
        say(demo, POLE + " Acum.", execute_incident=True)
    with pytest.raises(ValueError, match="event key"):
        answer_demo(demo[0], demo[1]["customer"], POLE, event_key="", connection_id=demo[2], execute_incident=True)
    assert counts(demo[0]) == before


@pytest.mark.parametrize("status", ["reconciling", "cancelled", "succeeded"])
def test_unpersisted_or_unsuccessful_result_never_claims_success(demo, monkeypatch, status):
    monkeypatch.setattr(
        demo[0], "confirm", lambda actor, proposal: {"status": status, "command_id": "synthetic-unsaved"}
    )
    result = say(demo, execute_incident=True)
    assert "Am înregistrat" not in result["reply"] and SAFETY in result["reply"]
    assert result["provenance"]["write_executed"] is False
    assert counts(demo[0]) == (1, 0, 0, 0)


def test_real_pending_command_is_not_success_and_retries_same_command(demo, monkeypatch):
    service = demo[0]

    def unavailable(*args, **kwargs):
        raise RuntimeError("synthetic storage failure")

    with monkeypatch.context() as patch:
        patch.setattr(service, "_apply", unavailable)
        pending = say(demo, execute_incident=True)
    assert pending["command"]["status"] == "reconciling"
    assert pending["provenance"]["write_executed"] is False
    assert "Am înregistrat" not in pending["reply"] and SAFETY in pending["reply"]
    assert counts(service) == (1, 1, 0, 0)
    recovered = say(demo, execute_incident=True)
    assert recovered["command"]["command_id"] == pending["command"]["command_id"]
    assert recovered["command"]["status"] == "succeeded"
    assert counts(service) == (1, 1, 1, 0)
