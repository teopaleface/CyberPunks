"""Exercise the real local workspace with three independently authenticated sessions.

Uses only synthetic demo accounts. Passwords and cookies never enter the report.
Run with uv run python scripts/daybreak_acceptance.py after starting the runtime.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from contextlib import ExitStack
from urllib.parse import urlsplit

import httpx
from daybreak_runtime import ROOT, read_private_env


def checked(response: httpx.Response, expected: int = 200):
    if response.status_code != expected:
        raise AssertionError(f"{response.request.method} {response.request.url.path}: expected {expected}, got {response.status_code}")
    return response.json()


def prepare(client: httpx.Client, action: str, data: dict):
    return checked(client.post("/api/operations/proposals", json={"action": action, "data": data, "scenario": "demo-vara"}))


def confirm(client: httpx.Client, proposal: dict):
    result = checked(client.post(f"/api/operations/proposals/{proposal['proposal_id']}/confirm", json={}))
    assert result["status"] == "succeeded", result.get("status")
    return result


def context(client: httpx.Client):
    return checked(client.get("/api/operations/context", params={"scenario": "demo-vara"}))


def main() -> None:
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("--chat", action="store_true", help="Also call the real Codex conversation provider for each account")
    args.add_argument("--base", default="http://127.0.0.1:3870", help="Explicit site origin for authorized synthetic acceptance")
    parsed = args.parse_args()
    target = urlsplit(parsed.base)
    if target.username or target.password or target.path not in ("", "/") or target.query or target.fragment or not (target.scheme == "https" or parsed.base == "http://127.0.0.1:3870"):
        args.error("Use an HTTPS origin or the default private local origin")
    env = read_private_env()
    base = parsed.base.rstrip("/")
    report = {"synthetic": True, "environment": "local" if target.hostname == "127.0.0.1" else "public", "checks": [], "conversation": []}

    def passed(name: str):
        report["checks"].append(name)
        print("PASS", name, flush=True)

    with ExitStack() as stack:
        clients = {}
        for role in ("customer", "technician", "dispatcher"):
            client = stack.enter_context(httpx.Client(base_url=base, headers={"origin": base}, timeout=130))
            checked(client.post("/api/cont/intrare", json={"email": env[f"DAYBREAK_DEMO_{role.upper()}_EMAIL"],
                                                         "password": env[f"DAYBREAK_DEMO_{role.upper()}_PASSWORD"]}))
            assert context(client)["actor"]["role"] == role
            clients[role] = client
            passed(f"{role}: independent authenticated session")
        customer, technician, dispatcher = (clients[k] for k in ("customer", "technician", "dispatcher"))
        initial = {role: context(client) for role, client in clients.items()}
        point = initial["customer"]["connections"][0]
        binding = next(c for c in initial["dispatcher"]["connections"] if c["connection_id"] == point["connection_id"])
        assert binding.get("meter_id"), "This acceptance story needs the provisioned assigned meter scenario. Prepare a new runtime."
        wid = binding["work_item_id"]
        assert any(w["work_item_id"] == wid for w in initial["technician"]["work_items"])
        assert initial["customer"]["work_items"] == []
        assert "routes" not in initial["customer"]["plan"]
        passed("customer: internal work items and global routes stay private")

        for client in (customer, technician):
            response = client.post("/api/operations/proposals", json={"action": "approve_plan", "data": {"plan_id": initial["dispatcher"]["plan"]["plan_id"]}})
            assert response.status_code == 403
        passed("customer and technician: dispatcher approvals refused")
        denied = customer.post("/api/operations/proposals", json={"action": "create_case", "data": {"connection_id": "UNOWNED-SYNTHETIC-POINT", "symptom": "Test access denial"}})
        assert denied.status_code in (403, 404)
        passed("customer: cannot create a case for another connection")

        symptom = f"Synthetic acceptance test {uuid.uuid4().hex[:8]}: the meter display has stopped changing."
        proposal = prepare(customer, "create_case", {"connection_id": point["connection_id"], "symptom_type": "meter", "symptom": symptom})
        before = context(customer)
        assert not any(c["symptom"] == symptom for c in before["cases"])
        passed("unconfirmed proposal: no case created")
        command = confirm(customer, proposal)
        repeated = confirm(customer, proposal)
        assert repeated["command_id"] == command["command_id"]
        case = command["result"]["case"]
        case_id = case["case_id"]
        assert case["assessment"]["status"] == "available"
        assert case["assessment"]["prediction_id"] and case["assessment"]["model_version"]
        passed("confirmed case: one command and a real compatible local prediction")
        for role, client in clients.items():
            assert any(c["case_id"] == case_id for c in context(client)["cases"])
        passed("shared case: visible in all three authorized sessions")

        current_plan = context(dispatcher)["plan"]
        approval = confirm(dispatcher, prepare(dispatcher, "approve_plan", {"plan_id": current_plan["plan_id"]}))
        assert approval["result"]["effect"]["effect_verified"] is True
        assert context(technician)["next_stop"] is not None
        passed("dispatcher approval: real planner effect and approved technician route")

        verdict = prepare(technician, "record_verdict", {"work_item_id": wid, "outcome": "confirmed", "case_id": case_id, "note": "Synthetic acceptance inspection; defect confirmed, repair not performed."})
        saved = confirm(technician, verdict)
        assert confirm(technician, verdict)["command_id"] == saved["command_id"]
        for role, client in clients.items():
            current_case = next(c for c in context(client)["cases"] if c["case_id"] == case_id)
            assert current_case["status"] == "verification_after_visit"
            assert current_case["verdict"]["outcome"] == "confirmed"
            if role == "customer":
                assert current_case["verdict"] == {"outcome": "confirmed", "repair_confirmed": False}
        assert saved["result"]["repaired"] is False
        passed("field confirmation: shared follow-up state, no false repair claim, no duplicate")

        stale = prepare(customer, "set_availability", {"case_id": case_id, "start": "2025-07-08T10:00:00+03:00", "end": "2025-07-08T12:00:00+03:00"})
        confirm(customer, prepare(customer, "request_human", {"case_id": case_id, "reason": "Synthetic acceptance: ask a dispatcher to review next steps."}))
        assert customer.post(f"/api/operations/proposals/{stale['proposal_id']}/confirm", json={}).status_code == 409
        passed("changed case: an old availability proposal cannot overwrite newer events")

        if parsed.chat:
            for role, client in clients.items():
                started = time.perf_counter()
                response = client.post("/api/conversation/chat", json={"message": "Salut! Ce este cunoscut despre cazul meu?" if role == "customer" else "Summarize the current plan for my role.", "history": [], "scenario": "demo-vara", "selection": {"case_id": case_id}})
                data = checked(response)
                assert data["provider"] == "codex-cli-chatgpt"
                assert data["provenance"]["write_executed"] is False
                report["conversation"].append({"role": role, "provider": data["provider"], "seconds": round(time.perf_counter()-started, 2), "reply": data["reply"]})
                passed(f"{role}: real subscription-backed Codex conversation")

        for client in clients.values():
            checked(client.post("/api/cont/iesire", json={}))
            assert client.get("/api/operations/context").status_code == 401
        passed("logout: all three sessions lose private API access")
    output = ROOT / "outputs" / "runtime" / ("acceptance-live.json" if report["environment"] == "public" else "acceptance.json")
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(f"Saved nonsecret acceptance evidence: {output}")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, httpx.HTTPError) as exc:
        print(f"FAIL {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
