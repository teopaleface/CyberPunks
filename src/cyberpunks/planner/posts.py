"""Posturile de transformare, unitatea comună pentru A, bilanț și C: harta (lei pierduți pe lună) și pagina postului.

Lei pierduți vin din lucrările de bilanț (sursa A, `asset_type: transformer_post`), din `extra.post_excess_loss_lei_month`
(sau, pentru contoarele confirmate, din `extra.fusion`). Culoarea: verde / galben / roșu după pragurile din
config/planner.yaml (`posts`). Registrul complet al posturilor îl deține firul C (`cyberpunks.c_prosumatori.posts`);
dacă există, posturile fără lucrări apar și ele pe hartă (verzi).
"""

from __future__ import annotations

from typing import Any

from cyberpunks.planner.settings import Settings


def _post_of(wi: dict[str, Any]) -> str | None:
    if wi.get("asset_type") == "transformer_post":
        return wi.get("asset_id")
    extra = wi.get("extra") or {}
    return extra.get("post_id") or (extra.get("fusion") or {}).get("post_id")


def _color(loss: float | None, settings: Settings) -> str:
    if loss is None:
        return "necunoscut"
    red = float(settings.rule("posts", "red_lei_month", default=600))
    yellow = float(settings.rule("posts", "yellow_lei_month", default=200))
    return "rosu" if loss >= red else ("galben" if loss >= yellow else "verde")


def _registry() -> list[dict[str, Any]]:
    try:
        from cyberpunks.c_prosumatori.posts import load_posts  # registrul firului C, dacă există
    except ImportError:
        return []
    try:
        rows = load_posts()
    except Exception:  # noqa: BLE001 - harta merge și fără registru
        return []
    if hasattr(rows, "to_dict"):
        rows = rows.to_dict("records")
    return [dict(r) for r in rows]


def overview(plan: dict[str, Any] | None, items: list[dict[str, Any]], settings: Settings) -> list[dict[str, Any]]:
    decisions = {d["work_item_id"]: d for d in (plan or {}).get("decisions", [])}
    posts: dict[str, dict[str, Any]] = {}

    def entry(pid: str) -> dict[str, Any]:
        return posts.setdefault(pid, {
            "post_id": pid, "lat": None, "lon": None, "zone_id": None, "label": pid, "loss_lei_month": None, "loss_kwh_day": None,
            "diagnosis": None, "bilant_score": None, "bilant_work_item_id": None, "bilant_decision": None, "bilant_rule_id": None,
            "voltage_p90_pu": None, "c_work_item_id": None, "c_decision": None, "c_rule_id": None,
            "meters_flagged": 0, "meter_work_item_ids": [], "synthetic": True, "in_registry": False,
        })

    for wi in items:
        pid = _post_of(wi)
        if not pid:
            continue
        e = entry(pid)
        d = decisions.get(wi["work_item_id"]) or {}
        loc = wi.get("location") or {}
        extra = wi.get("extra") or {}
        e["synthetic"] = e["synthetic"] and bool((wi.get("data_quality") or {}).get("synthetic", True))
        if wi.get("asset_type") == "transformer_post" and e["lat"] is None:
            e.update(lat=loc.get("lat"), lon=loc.get("lon"), zone_id=loc.get("zone_id"), label=loc.get("label") or pid)
        if wi["source"] == "A" and wi.get("asset_type") == "transformer_post":
            loss = extra.get("post_excess_loss_lei_month")
            e.update(
                loss_lei_month=float(loss) if isinstance(loss, (int, float)) else e["loss_lei_month"],
                loss_kwh_day=extra.get("post_excess_loss_kwh_day", e["loss_kwh_day"]), diagnosis=wi["prediction"].get("label"),
                bilant_score=wi["prediction"].get("score"), bilant_work_item_id=wi["work_item_id"],
                bilant_decision=d.get("decision"), bilant_rule_id=d.get("rule_id"),
            )
        elif wi["source"] == "C":
            pi = wi["prediction"].get("point_interval")
            e.update(voltage_p90_pu=pi[1] if pi else wi["prediction"].get("point_estimate"), c_work_item_id=wi["work_item_id"],
                     c_decision=d.get("decision"), c_rule_id=d.get("rule_id"))
        elif wi["source"] == "A":
            e["meters_flagged"] += 1
            e["meter_work_item_ids"].append(wi["work_item_id"])
            fusion = extra.get("fusion") or {}
            if e["loss_lei_month"] is None and isinstance(fusion.get("post_excess_loss_lei_month"), (int, float)):
                e["loss_lei_month"] = float(fusion["post_excess_loss_lei_month"])
            if e["lat"] is None:
                e.update(lat=loc.get("lat"), lon=loc.get("lon"), zone_id=loc.get("zone_id"))
    for row in _registry():
        pid = str(row.get("post_id", ""))
        if not pid:
            continue
        e = entry(pid)
        e["in_registry"] = True
        for key in ("lat", "lon", "zone_id"):
            if e[key] is None and row.get(key) is not None:
                e[key] = row[key]
        if e["loss_lei_month"] is None and e["bilant_work_item_id"] is None:
            e["loss_lei_month"] = 0.0  # în registru, fără lipsă semnalată de bilanț
        e["kva"] = row.get("kva")
        if row.get("label") and e["label"] == pid:
            e["label"] = row["label"]
    out = []
    for e in posts.values():
        e["color"] = _color(e["loss_lei_month"], settings)
        out.append(e)
    out.sort(key=lambda e: -(e["loss_lei_month"] or 0.0))
    return out


def detail(post_id: str, plan: dict[str, Any] | None, items: list[dict[str, Any]], settings: Settings) -> dict[str, Any] | None:
    summary = next((p for p in overview(plan, items, settings) if p["post_id"] == post_id), None)
    if summary is None:
        return None
    decisions = {d["work_item_id"]: d for d in (plan or {}).get("decisions", [])}
    related = [wi for wi in items if _post_of(wi) == post_id]
    return {
        **summary,
        "work_items": [{**wi, "decision": decisions.get(wi["work_item_id"])} for wi in related],
        "series_ids": [wi["work_item_id"] for wi in related],
    }
