"""Asocieri de DEMO SINTETICE pe activele reale ale planului complet local."""

from typing import Any

DEMO_ORGANIZATION = "daybreak-demo"
DEMO_CONNECTION = "CONN-DEMO-001"


def post_of(w: dict[str, Any]) -> str | None:
    if w.get("asset_type") == "transformer_post":
        return w.get("asset_id")
    return w.get("extra", {}).get("post_id") or w.get("extra", {}).get("fusion", {}).get("post_id")


def demo_binding(plan: dict, items: list[dict], scenario: str) -> dict | None:
    """Preferă C atribuit, apoi contor A atribuit cu predicție compatibilă.

    Asocierea identifică un punct sintetic și o lucrare demonstrabilă. Cazurile
    folosesc separat ID-ul exact al evaluării compatibile cu simptomul.
    """
    indexed = {w["work_item_id"]: w for w in items}
    voltage_posts = {post_of(w) for w in items if w["source"] == "C"}
    candidates = []
    for route in plan.get("routes", []):
        for stop in route.get("stops", []):
            w = indexed.get(stop["work_item_id"])
            if not w or not post_of(w):
                continue
            if w["source"] == "C":
                priority = 0
            elif w["source"] == "A" and w["asset_type"] == "meter":
                priority = 1 if post_of(w) in voltage_posts else 2
            else:
                priority = 3 if post_of(w) in voltage_posts else 4
            candidates.append((priority, w["work_item_id"], route["crew_id"], w))
    if not candidates:
        return None
    _, wid, crew, w = min(candidates, key=lambda x: x[:3])
    return {
        "connection_id": DEMO_CONNECTION,
        "organization_id": DEMO_ORGANIZATION,
        "scenario": scenario,
        "label": "Synthetic demo connection",
        "post_id": post_of(w),
        "meter_id": w["asset_id"] if w["asset_type"] == "meter" else None,
        "work_item_id": wid,
        "crew_id": crew,
        "supported_symptom_types": ["voltage"]
        if w["source"] == "C"
        else (["meter"] if w["asset_type"] == "meter" else ["other"]),
        "synthetic": True,
        "association_source": "synthetic provisioned membership; exact post in complete local plan",
        "association_plan_id": plan["plan_id"],
    }
