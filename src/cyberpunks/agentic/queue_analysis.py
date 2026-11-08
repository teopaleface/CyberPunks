"""Analyze existing full-plan decisions without rerunning capacity rules."""

from copy import deepcopy


def analyze_queue(context):
    rows = []
    ids = set()
    for index, item in enumerate(context.get("work_items", [])):
        decision = item.get("decision") or {}
        if decision.get("decision") != "human_review":
            continue
        wid = item["work_item_id"]
        if wid in ids:
            raise ValueError("Duplicate work item")
        ids.add(wid)
        assessment = item.get("assessment") or {}
        valid = assessment.get("status") == "available" and all(
            assessment.get(k) for k in ("prediction_id", "model_id", "model_version")
        )
        valid = valid and assessment.get("scenario") == context.get("scenario")
        valid = valid and assessment.get("target_date") == context["plan"].get("plan_date")
        valid = valid and bool(decision.get("rule_id"))
        rows.append(
            {
                "work_item_id": wid,
                "recommendation": (
                    "request_additional_crews"
                    if decision.get("rule_id") == "R-B-REGION-CAP"
                    else item.get("recommended_action") or "human_review"
                )
                if valid
                else "abstain",
                "title": (item.get("location") or {}).get("address") or item.get("asset_id") or wid,
                "reason": decision.get("reason_ro") or decision.get("reason") or "Necesită evaluare umană."
                if valid
                else assessment.get("reason") or "Evaluare invalidă sau dovezi incomplete.",
                "assessment": deepcopy(assessment),
                "decision": deepcopy(decision),
                "evidence": {
                    "path": f"/work_items/{index}",
                    "source": deepcopy(item),
                    "plan_version": context["plan"]["version"],
                },
            }
        )
    expected = [r["work_item_id"] for r in rows]
    return {
        "items": rows,
        "expected_ids": expected,
        "analyzed_ids": expected.copy(),
        "complete": True,
        "total": len(rows),
        "plan_version": context["plan"]["version"],
    }
