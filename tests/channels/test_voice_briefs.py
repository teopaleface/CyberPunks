"""Private synthetic demo briefs on an isolated, complete fresh operational copy."""

import os
import shutil
from copy import deepcopy
from pathlib import Path
from time import perf_counter

import pytest

from cyberpunks.channels.voice_briefs import EQUIPMENT_UNKNOWN, SAFETY, answer_demo, trusted_next_stop
from cyberpunks.operations.models import Actor, OperationError
from cyberpunks.operations.service import OperationsService
from cyberpunks.planner import feedback

POLE = "sunt client ppc vreau să raportez că mi-a picat stâlpul de curent"
QUEUE = "câte tichete am astăzi și câte sunt de prioritate ridicată"
ROUTE = "ce am de făcut astăzi? trebuie echipament?"


@pytest.fixture
def demo(tmp_path):
    source = Path(os.environ["DAYBREAK_OPERATIONS_TEST_DATA"])
    assert (source / "plans/demo-vara/inputs").is_dir(), "Full fresh operational data required"
    target = tmp_path / "synthetic-full-copy"
    # Coordinator supplied a complete hash-matched live-data copy with no credentials
    # or automation configuration. Keep every row and existing plan, not a replan/sample.
    shutil.copytree(source, target)
    operations = OperationsService(target, tmp_path / "synthetic.sqlite3")
    b = operations.demo_bindings()
    base = {"organization_id": b["organization_id"]}
    actors = {
        "customer": Actor(user_id="synthetic-client", role="customer", connection_ids=b["connection_ids"], **base),
        "dispatcher": Actor(user_id="synthetic-dispatch", role="dispatcher", permissions=b["permissions"], **base),
        "technician": Actor(user_id="synthetic-tech", role="technician", crew_id=b["crew_id"], **base),
    }
    return operations, actors, b, target


def brief(demo, role, message, **kwargs):
    s, actors, _binding, _ = demo
    return answer_demo(s, actors[role], message, event_key="synthetic-event-1", **kwargs)


def rows(demo, table):
    with demo[0].db.connect() as db:
        return db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]


def approve(demo):
    feedback.approve_route("demo-vara", demo[1]["technician"].crew_id, "synthetic-reviewer", out_root=demo[3])


def test_full_queue_exact_25_safety_and_latency(demo):
    context = demo[0].context(demo[1]["dispatcher"])
    assert len(context["work_items"]) >= 600
    queue = [w for w in context["work_items"] if (w.get("decision") or {}).get("decision") == "human_review"]
    assert len(queue) == 25
    safety = sum(w["impact"]["safety_flag"] is True for w in queue)
    start = perf_counter()
    result = brief(demo, "dispatcher", QUEUE)
    assert perf_counter() - start < 1
    assert result["reply"] == (
        f"În coada de revizuire, în scenariul demo, sunt 25 tichete, dintre care {safety} cu semnal de siguranță."
    )
    assert "impact.safety_flag" in result["provenance"]["priority_criterion"]
    assert set(result["provenance"]["work_item_ids"]) == {w["work_item_id"] for w in queue}
    assert len(result["reply"].split()) <= 30
    assert result["proposal"] is None
    all_work = brief(demo, "dispatcher", "Câte lucrări sunt în tot planul?")
    assert all_work["provenance"]["total"] == len(context["work_items"])
    assert all_work["provenance"]["queue_scope"] == "all_work_items"


@pytest.mark.parametrize(
    "message",
    [
        POLE,
        "sunt clientppc vreau sa raportez ca mi-a picat stalpul de curent",
        "mi-a picat stalpu de curent",
        "Sunt client PPC. Vreau să raportez că a căzut un stâlp de curent.",
    ],
)
def test_urgent_real_proposal_only_snapshot_idempotency_and_latency(demo, message):
    s, actors, b, _ = demo
    start = perf_counter()
    result = brief(demo, "customer", message, connection_id=b["connection_ids"][0])
    assert perf_counter() - start < 1
    p = result["proposal"]
    assert p["action"] == "request_human" and p["requires_confirmation"] is True
    assert p["data"]["priority"] == "urgent"
    assert p["data"]["connection_id"] == b["connection_ids"][0]
    assert "Demo sintetic" in p["data"]["reason"] and message in p["data"]["reason"]
    assert p["data"]["plan_version"] == result["provenance"]["plan_version"]
    assert result["provenance"]["snapshot"]["message"] == message
    assert result["provenance"]["event_key"] == "synthetic-event-1"
    assert result["provenance"]["write_executed"] is False
    assert result["reply"].startswith(SAFETY) and "Confirm" in result["reply"]
    assert len(result["reply"].split()) <= 35
    again = brief(demo, "customer", message, connection_id=b["connection_ids"][0])
    assert again["proposal"]["proposal_id"] == p["proposal_id"]
    assert s.proposal(actors["customer"], p["proposal_id"]) == p
    assert rows(demo, "proposals") == 1
    for table in ("commands", "events", "cases"):
        assert rows(demo, table) == 0


@pytest.mark.parametrize("selection", [None, "synthetic-foreign-connection"])
def test_missing_or_foreign_server_connection_asks_one_question(demo, selection):
    result = brief(demo, "customer", POLE, connection_id=selection)
    assert result["proposal"] is None and result["reply"].count("?") == 1
    assert SAFETY in result["reply"] and rows(demo, "proposals") == 0


@pytest.mark.parametrize(
    "message",
    [
        'Clientul a spus "mi-a picat stâlpul de curent".',
        "Dacă mi-a picat stâlpul de curent, ce aș spune?",
        "Nu mi-a picat stâlpul de curent.",
        "Nu vreau să raportez că mi-a picat stâlpul de curent.",
        "Un exemplu: mi-a picat stâlpul de curent.",
        "Mi-a picat stâlpul de curent? Poate.",
        "Clientul a spus că mi-a picat stâlpul de curent.",
        "N-a picat stâlpul de curent.",
        "Aș raporta că mi-a picat stâlpul de curent.",
        "Care este prognoza?",
    ],
)
def test_quotes_hypotheses_negations_unknown_defer_without_effects(demo, message):
    assert brief(demo, "customer", message, connection_id=demo[2]["connection_ids"][0]) is None
    assert rows(demo, "proposals") == rows(demo, "commands") == 0


def test_clear_outage_never_gets_fake_priority(demo):
    p = brief(demo, "customer", "Mi-a picat curentul", connection_id=demo[2]["connection_ids"][0])["proposal"]
    assert p["action"] == "create_case" and p["data"]["symptom_type"] == "outage"
    assert "priority" not in p["data"] and rows(demo, "cases") == 0


def test_own_approved_route_and_missing_equipment(demo):
    approve(demo)
    start = perf_counter()
    result = brief(demo, "technician", ROUTE)
    assert perf_counter() - start < 1
    assert result and EQUIPMENT_UNKNOWN in result["reply"]
    assert result["provenance"]["equipment_known"] is False
    assert result["provenance"]["crew_id"] == demo[1]["technician"].crew_id
    context = demo[0].context(demo[1]["technician"])
    routes, remaining, stop, by_id = trusted_next_stop(context, demo[1]["technician"])
    assert result["provenance"]["remaining"] == len(remaining)
    location = by_id[stop["work_item_id"]]["location"]
    source_label = location.get("address") or location["label"]
    place = source_label.split(",")[-1].replace("(sintetic)", "").strip()
    assert place in result["reply"]
    assert "MTR-" not in result["reply"] and "PT-" not in result["reply"]
    assert all(r["crew_id"] == demo[1]["technician"].crew_id for r in routes)
    assert len(result["reply"].split()) <= 45


def test_no_approval_foreign_approval_and_stale_approval_are_not_permission(demo):
    for name in ("approvals.json", "plan_approval.json"):
        (demo[3] / "plans/demo-vara" / name).unlink(missing_ok=True)
    result = brief(demo, "technician", ROUTE)
    assert "nu este încă aprobat" in result["reply"]
    context = demo[0].context(demo[1]["technician"])
    context["next_stop_status"] = "approved_plan"  # alone must never authorize a crew
    crew = demo[1]["technician"].crew_id
    for approval in ({"crew_id": "other-crew", "stale": False}, {"crew_id": crew, "stale": True}):
        context["plan"]["approvals"] = [approval]
        assert trusted_next_stop(context, demo[1]["technician"])[0] == []


def test_visited_stop_skipped_and_canonical_reason(demo):
    approve(demo)
    s, actors, _, _ = demo
    context = s.context(actors["technician"])
    first = context["next_stop"]["work_item_id"]
    p = s.prepare(actors["technician"], "record_verdict", {"work_item_id": first, "outcome": "not_found"})
    s.confirm(actors["technician"], p["proposal_id"])
    result = brief(demo, "technician", ROUTE)
    assert result["provenance"]["next_stop"]["work_item_id"] != first
    why = brief(demo, "technician", "care este următoarea oprire și de ce")
    assert why and why["provenance"]["reason_source"].endswith("reason_for_visit")
    assert "=" not in why["reply"] and len(why["reply"].split()) <= 45


def test_actor_isolation_and_unknown_queries(demo):
    for role, question in (("customer", QUEUE), ("technician", QUEUE), ("dispatcher", POLE)):
        assert brief(demo, role, question) is None
    foreign = demo[1]["dispatcher"].model_copy(update={"organization_id": "foreign"})
    with pytest.raises(OperationError):
        answer_demo(demo[0], foreign, QUEUE, event_key="synthetic")
    assert rows(demo, "proposals") == 0


def test_safety_count_ignores_ml_priority_score(demo, monkeypatch):
    original = demo[0].context
    context = deepcopy(original(demo[1]["dispatcher"]))
    queue = [w for w in context["work_items"] if (w.get("decision") or {}).get("decision") == "human_review"]
    for i, item in enumerate(queue):
        item["impact"]["safety_flag"] = i == 24
        item["decision"]["priority_score"] = 999999 if i != 24 else 0
    monkeypatch.setattr(demo[0], "context", lambda actor, scenario: context)
    result = brief(demo, "dispatcher", QUEUE)
    assert result["provenance"]["safety_count"] == 1
    assert "1 cu semnal de siguranță" in result["reply"]


def test_equipment_only_explicit_fields_of_remaining_own_stops(demo, monkeypatch):
    approve(demo)
    context = deepcopy(demo[0].context(demo[1]["technician"]))
    for item in context["work_items"]:
        item["extra"]["required_equipment"] = ["trusă de măsurare sintetică"]
    monkeypatch.setattr(demo[0], "context", lambda actor, scenario: context)
    result = brief(demo, "technician", ROUTE)
    assert result["provenance"]["equipment_known"] is True
    assert "trusă de măsurare sintetică" in result["reply"]
    del context["work_items"][-1]["extra"]["required_equipment"]
    assert EQUIPMENT_UNKNOWN in brief(demo, "technician", ROUTE)["reply"]


def test_exact_event_cannot_be_reused_for_different_report(demo):
    cid = demo[2]["connection_ids"][0]
    brief(demo, "customer", POLE, connection_id=cid)
    with pytest.raises(OperationError, match="idempotency"):
        brief(demo, "customer", POLE + " acum", connection_id=cid)
    assert rows(demo, "proposals") == 1


def test_ambiguous_connection_and_missing_event_never_prepare(demo, monkeypatch):
    s, actors, b, _ = demo
    context = s.context(actors["customer"])
    context["connections"] *= 2
    with monkeypatch.context() as patch:
        patch.setattr(s, "context", lambda actor, scenario: context)
        result = brief(demo, "customer", POLE, connection_id=b["connection_ids"][0])
        assert result["proposal"] is None and result["reply"].count("?") == 1
    with pytest.raises(ValueError, match="event key"):
        answer_demo(s, actors["customer"], POLE, event_key="", connection_id=b["connection_ids"][0])
    assert rows(demo, "proposals") == 0


def test_completed_route_and_wrong_crew_next_stop_are_not_instructions(demo, monkeypatch):
    approve(demo)
    context = deepcopy(demo[0].context(demo[1]["technician"]))
    context["plan"]["routes"].insert(
        0,
        {
            "crew_id": "synthetic-foreign-crew",
            "stops": [{"work_item_id": "synthetic-foreign-stop", "title": "SECRET FOREIGN STOP"}],
        },
    )
    context["next_stop"] = context["plan"]["routes"][0]["stops"][0]
    monkeypatch.setattr(demo[0], "context", lambda actor, scenario: context)
    result = brief(demo, "technician", ROUTE)
    assert "FOREIGN" not in result["reply"]
    for item in context["work_items"]:
        item["findings"] = [{"outcome": "not_found"}]
    completed = brief(demo, "technician", ROUTE)
    assert completed["provenance"]["remaining"] == 0
    assert "nu mai ai opriri" in completed["reply"]


def test_real_asr_incident_asks_for_clarification_instead_of_guessing(demo):
    result = brief(demo, "customer", "Sunt client TPC. A căzut astăzi de curent și vreau să, ăăă, raportez incidentul.")
    assert result["reply"] == "Te referi la un stâlp căzut sau la o întrerupere de curent?"
    assert result["proposal"] is None
    assert rows(demo, "proposals") == 0 and rows(demo, "commands") == 0
