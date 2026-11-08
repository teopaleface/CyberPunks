"""Bounded, authorized task execution. Confirmation stays in the operations API."""

from .evidence import validate_analysis
from .queue_analysis import analyze_queue
from .snapshots import authorized_snapshot


class AgenticCoordinator:
    def __init__(self, operations, store):
        self.operations, self.store = operations, store

    def run(self, actor, request, *, task_id=None):
        context = authorized_snapshot(self.operations, actor, request.scenario)
        if request.goal == "analyze_queue" and actor.role != "dispatcher":
            raise PermissionError("Only dispatchers can analyze the review queue")
        task = self.store.get(actor, task_id) if task_id else self.store.create(actor, request, context["plan_version"])
        if task.plan_version != context["plan_version"]:
            raise ValueError("Plan changed; start a fresh task")
        if task.status not in {"queued", "running"}:
            return task
        token = self.store.claim(actor, task.task_id, seconds=30)
        if token is None:
            return self.store.get(actor, task.task_id)

        def finish(**fields):
            fresh = authorized_snapshot(self.operations, actor, request.scenario)
            if fresh["plan_version"] != context["plan_version"]:
                raise ValueError("Plan version changed; start a fresh task")
            return self.store.update(actor, task.task_id, claim_token=token, **fields)

        ro = request.language == "ro"
        try:
            if request.goal == "analyze_queue":
                result = analyze_queue(context)
                validate_analysis(context, result)
                reply = (
                    f"Am analizat toate cele {result['total']} cazuri. Recomandările și motivele sunt în listă; schimbările cer confirmarea ta."
                    if ro
                    else f"Analyzed all {result['total']} cases. Recommendations and reasons are listed; changes require your confirmation."
                )
            elif request.goal == "prepare_operation":
                from .effects import prepare_operation

                proposal = prepare_operation(self.operations, actor, request, context)
                return finish(
                    status="awaiting_confirmation",
                    proposal=proposal,
                    reply="Propunerea este pregătită. Confirmă în aplicație."
                    if ro
                    else "Proposal ready. Confirm in the application.",
                )
            elif request.goal == "route_brief":
                if actor.role == "customer":
                    raise PermissionError("Route unavailable for this account")
                approved_crews = {a["crew_id"] for a in context["plan"].get("approvals", []) if not a.get("stale")}
                routes = [
                    r
                    for r in context["plan"].get("routes", [])
                    if context["plan"].get("approved") or r.get("crew_id") in approved_crews
                ]
                if not routes:
                    return finish(
                        status="needs_information",
                        reply="Traseul nu este încă aprobat." if ro else "The route is not approved yet.",
                    )
                by_id = {item["work_item_id"]: item for item in context.get("work_items", [])}
                routes = [
                    {
                        **route,
                        "stops": [
                            {
                                **stop,
                                "title": (by_id.get(stop.get("work_item_id"), {}).get("location") or {}).get("address")
                                or by_id.get(stop.get("work_item_id"), {}).get("asset_id")
                                or "Vizită planificată",
                                "reason": (by_id.get(stop.get("work_item_id"), {}).get("decision") or {}).get(
                                    "reason_ro", ""
                                ),
                            }
                            for stop in route.get("stops", [])
                        ],
                    }
                    for route in routes
                ]
                result = {
                    "routes": routes,
                    "next_stop": context.get("next_stop"),
                    "next_stop_status": context.get("next_stop_status"),
                }
                stop = context.get("next_stop") or {}
                next_item = by_id.get(stop.get("work_item_id"), {})
                location = next_item.get("location") or stop.get("location") or {}
                label = (
                    location.get("address")
                    or location.get("city")
                    or next_item.get("asset_id")
                    or "următoarea vizită din traseu"
                )
                reply = (
                    (
                        f"Următoarea oprire aprobată este {label}. Orele din raport sunt planificate."
                        if ro
                        else f"Your next approved stop is {label}. Report times are planned."
                    )
                    if label
                    else (
                        "Traseul aprobat este în raport; orele sunt planificate."
                        if ro
                        else "Your approved route is in the report; times are planned."
                    )
                )
                if not stop:
                    reply = (
                        "Nu există o oprire următoare neverificată în traseul aprobat. Consultă constatările și planul."
                        if actor.role == "technician" and ro else
                        "There is no remaining unvisited approved stop. Review the findings and plan."
                        if actor.role == "technician" else
                        "Traseele aprobate sunt în raport." if ro else "The approved routes are in the report."
                    )
            else:
                cases = context.get("cases", [])
                if request.case_id:
                    cases = [c for c in cases if c.get("case_id") == request.case_id]
                if len(cases) != 1:
                    return finish(
                        status="needs_information",
                        reply="Selectează sesizarea pe care vrei să o verific."
                        if ro
                        else "Select the case you want to check.",
                    )
                result = {"cases": cases}
                reply = (
                    "Starea verificată a sesizării este în raport. Repararea nu este confirmată."
                    if ro
                    else "The verified case status is in the report. Repair is not confirmed."
                )
            return finish(status="completed", result=result, reply=reply)
        except Exception:
            try:
                self.store.update(
                    actor,
                    task.task_id,
                    claim_token=token,
                    status="failed",
                    error="Task could not be verified. Start a fresh task.",
                )
            except (ValueError, PermissionError):
                pass
            raise
