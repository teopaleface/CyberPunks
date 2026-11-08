"""Reports consume a freshly authorized OperationsService.context, never raw storage."""

from datetime import UTC, datetime


def build_report_data(context, analysis=None, language="ro"):
    role = context["actor"]["role"]
    if role not in {"dispatcher", "technician", "customer"}:
        raise ValueError("Unsupported report role")
    plan = context.get("plan") or {}
    fields = {
        "dispatcher": ("title", "work_item_id", "recommendation", "reason"),
        "technician": ("title", "work_item_id", "eta", "duration_min", "seq", "travel_km", "reason", "status"),
        "customer": ("case_id", "status", "next_step"),
    }[role]
    if role == "dispatcher" and analysis is None:
        from .queue_analysis import analyze_queue

        analysis = analyze_queue(context)
    if role == "dispatcher":
        source = (analysis or {}).get("items", context.get("work_items", []))
    elif role == "technician":
        source = [s for r in plan.get("routes", []) for s in r.get("stops", [])]
    else:
        source = context.get("cases", [])
    rows = [{k: str(row[k]) for k in fields if k in row and isinstance(row[k], (str, int, float))} for row in source]
    titles = {"dispatcher": "Lista dispecerului", "technician": "Traseu planificat", "customer": "Starea sesizării"}
    state = (
        "approved"
        if role == "technician" and (plan.get("approved") or context.get("next_stop_status") == "approved_plan")
        else "proposed"
    )
    data = {
        "kind": role,
        "title": titles[role],
        "scenario": context["scenario"],
        "plan_version": str(context.get("plan_version", plan.get("plan_version", plan.get("version", "unknown")))),
        "generated_at": datetime.now(UTC).isoformat(),
        "historical_date": context.get("historical_date", plan.get("plan_date", "2025-07-08")),
        "synthetic": context.get("synthetic", True),
        "rows": rows,
        "state": state,
        "language": language,
    }
    data["text"] = "\n".join(
        [
            data["title"],
            f"Istoric: {data['historical_date']} | {state}",
            f"Generat: {data['generated_at']} | Versiune: {data['plan_version']}",
            "Include date sintetice" if data["synthetic"] else "Date istorice",
            *["; ".join(f"{k}: {v}" for k, v in row.items()) for row in rows],
        ]
    )
    return data
