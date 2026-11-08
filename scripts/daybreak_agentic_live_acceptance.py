"""Explicitly invoked agentic acceptance. Never prints response bodies or credentials."""

from __future__ import annotations

import argparse
import ipaddress
import json
import uuid
from contextlib import ExitStack
from datetime import UTC, datetime
from urllib.parse import urlsplit

import httpx
from daybreak_runtime import ROOT, read_private_env


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--chat", action="store_true")
    parser.add_argument(
        "--effects", action="store_true", help="Confirm a labeled synthetic current-plan approval; writes audit history"
    )
    args = parser.parse_args()
    url = urlsplit(args.base)
    local = url.hostname == "localhost"
    try:
        local = local or ipaddress.ip_address(url.hostname).is_loopback
    except ValueError:
        pass
    if (
        url.username
        or url.password
        or url.query
        or url.fragment
        or url.path not in ("", "/")
        or not (url.scheme == "https" or url.scheme == "http" and local)
    ):
        parser.error("--base must be an HTTPS origin or loopback HTTP origin without credentials")
    base = args.base.rstrip("/")
    report = {
        "started_at": datetime.now(UTC).isoformat(),
        "synthetic": True,
        "environment": "local" if local else "public",
        "checks": [],
        "ok": False,
    }
    stage = "initialization"

    def require(condition):
        if not condition:
            raise AssertionError("Acceptance assertion failed")

    def call(client, method, path, body=None, statuses=(200,)):
        response = client.request(method, path, json=body) if body is not None else client.request(method, path)
        if response.status_code not in statuses:
            raise RuntimeError(f"Unexpected HTTP status {response.status_code}")
        return response.json() if response.status_code == 200 else None

    def passed(name):
        report["checks"].append(name)
        print("PASS", name, flush=True)

    try:
        env = read_private_env()
        with ExitStack() as stack:
            clients = {}
            anonymous = stack.enter_context(httpx.Client(base_url=base, timeout=150))
            stage = "anonymous authorization"
            call(anonymous, "GET", "/api/operations/context", statuses=(401,))
            call(anonymous, "POST", "/api/conversation/tasks", {"goal": "analyze_queue"}, (401,))
            for role in ("dispatcher", "technician", "customer"):
                stage = f"{role} login"
                client = stack.enter_context(httpx.Client(base_url=base, headers={"origin": base}, timeout=150))
                clients[role] = client
                call(
                    client,
                    "POST",
                    "/api/cont/intrare",
                    {
                        "email": env[f"DAYBREAK_DEMO_{role.upper()}_EMAIL"],
                        "password": env[f"DAYBREAK_DEMO_{role.upper()}_PASSWORD"],
                    },
                )

            def context(role):
                return call(clients[role], "GET", "/api/operations/context?scenario=demo-vara")

            def task(role, goal, **fields):
                return call(
                    clients[role], "POST", "/api/conversation/tasks", {"goal": goal, "scenario": "demo-vara", **fields}
                )

            contexts = {r: context(r) for r in clients}
            stage = "context privacy"
            for role, ctx in contexts.items():
                require(ctx["actor"]["role"] == role)
            customer = contexts["customer"]
            require(customer["work_items"] == [] and "routes" not in customer["plan"])
            passed("independent sessions and customer context privacy")
            stage = "complete human review coverage"
            queue = task("dispatcher", "analyze_queue")
            require(queue["status"] == "completed")
            result = queue["result"]
            expected = [
                w["work_item_id"]
                for w in contexts["dispatcher"]["work_items"]
                if (w.get("decision") or {}).get("decision") == "human_review"
            ]
            actual = [w["work_item_id"] for w in result["items"]]
            require(len(actual) == len(set(actual)) and set(actual) == set(expected))
            require(result["complete"] is True and result["total"] == len(expected))
            require(set(result["expected_ids"]) == set(expected) == set(result["analyzed_ids"]))
            report["review_count"] = len(expected)
            path = "/api/conversation/tasks/" + queue["task_id"]
            require(call(clients["dispatcher"], "GET", path) == queue)
            for role in ("customer", "technician"):
                call(clients[role], "GET", path, statuses=(403, 404))
                call(clients[role], "POST", "/api/conversation/tasks", {"goal": "analyze_queue"}, (403, 404))
            call(anonymous, "GET", path, statuses=(401,))
            passed("exact queue coverage and task ownership")
            stage = "approved technician route"
            route = task("technician", "route_brief")
            plan = contexts["technician"]["plan"]
            crews = {a["crew_id"] for a in plan.get("approvals", []) if not a.get("stale")}
            eligible = [r for r in plan.get("routes", []) if plan.get("approved") or r.get("crew_id") in crews]
            if eligible:
                require(route["status"] == "completed")
                require(len(route["result"]["routes"]) == len(eligible))
                for actual_route, source in zip(route["result"]["routes"], eligible):
                    require(actual_route["crew_id"] == source["crew_id"])
                    require(
                        [s["work_item_id"] for s in actual_route["stops"]]
                        == [s["work_item_id"] for s in source["stops"]]
                    )
            else:
                require(route["status"] == "needs_information" and not route["result"].get("routes"))
            call(clients["customer"], "POST", "/api/conversation/tasks", {"goal": "route_brief"}, (403, 404))
            passed("technician route contains only approved stops")
            stage = "customer case selection"
            cases = customer.get("cases", [])
            require(bool(cases))
            selected = cases[-1]
            brief = task("customer", "case_brief", case_id=selected["case_id"])
            require(brief["status"] == "completed" and brief["result"]["cases"] == [selected])
            foreign = task("customer", "case_brief", case_id="SYNTHETIC-UNOWNED-" + uuid.uuid4().hex)
            require(foreign["status"] == "needs_information" and not foreign["result"].get("cases"))
            passed("customer brief matches explicitly selected authorized case")
            if args.chat:
                stage = "two turn Codex conversation"
                history = []
                for message in (
                    "Analizează întreaga coadă de evaluare umană.",
                    "Explică motivele recomandărilor fără să execuți schimbări.",
                ):
                    data = call(
                        clients["dispatcher"],
                        "POST",
                        "/api/conversation/chat",
                        {"message": message, "history": history, "scenario": "demo-vara"},
                    )
                    require(data["provider"] == "codex-cli-chatgpt" and bool(data["reply"]))
                    require(data["provenance"]["write_executed"] is False)
                    history.extend(
                        [{"role": "user", "content": message}, {"role": "assistant", "content": data["reply"]}]
                    )
                passed("two real dispatcher Codex turns without operational writes")
            if args.effects:
                stage = "synthetic current plan approval"
                current = context("dispatcher")["plan"]
                prepared = task(
                    "dispatcher",
                    "prepare_operation",
                    action="approve_plan",
                    request_key="synthetic-acceptance-" + uuid.uuid4().hex,
                    data={
                        "plan_id": current["plan_id"],
                        "note": "SYNTHETIC live acceptance: verify current-plan approval and idempotency. No field visit or repair claimed.",
                    },
                )
                require(prepared["status"] == "awaiting_confirmation")
                confirm_path = "/api/operations/proposals/" + prepared["proposal"]["proposal_id"] + "/confirm"
                first = call(clients["dispatcher"], "POST", confirm_path, {})
                second = call(clients["dispatcher"], "POST", confirm_path, {})
                require(first["status"] == "succeeded" and first["command_id"] == second["command_id"])
                resumed = call(
                    clients["dispatcher"], "POST", "/api/conversation/tasks/" + prepared["task_id"] + "/resume", {}
                )
                require(resumed["status"] == "completed")
                passed("synthetic plan approval confirmed once and passively resumed")
            report["ok"] = True
    except (AssertionError, RuntimeError, httpx.HTTPError, KeyError, TypeError, ValueError, OSError) as exc:
        # Never persist exception messages, request headers, response bodies, or chat text.
        report["failure"] = {"stage": stage, "type": type(exc).__name__}
    finally:
        output = ROOT / "outputs/runtime/agentic-live-acceptance.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print("PASS" if report["ok"] else "FAIL", "agentic acceptance; safe report:", output)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
