"""Generează exemplele din contracts/fixtures/ (date ILUSTRATIVE, nu ieșiri de model).

    uv run python contracts/make_fixtures.py

Firele le folosesc ca să lucreze în paralel înainte ca modelele reale să existe:
interfața și planificatorul pornesc de la aceste fișiere, apoi trec pe ieșirile reale.
"""

from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from cyberpunks.common.contracts import (
    Alert,
    AuditRecord,
    Decision,
    Notification,
    Plan,
    PlanSummary,
    Route,
    Series,
    SeriesAnnotation,
    SeriesPoint,
    Stop,
    WorkItem,
)

TZ = timezone(timedelta(hours=2))  # Europe/Bucharest iarna; vara e +03:00
OUT = Path(__file__).parent / "fixtures"
D = date(2026, 11, 9)
NOW = datetime(2026, 11, 8, 6, 0, tzinfo=TZ)


def pid() -> str:
    return str(uuid.uuid4())


def wi_a(asset: str, lat: float, lon: float, zone: str, score: float, label: str, abstain: bool = False) -> dict:
    value = 1425.0
    return {
        "work_item_id": f"A-{D:%Y%m%d}-{asset}",
        "source": "A",
        "kind": "meter_inspection",
        "asset_id": asset,
        "asset_type": "meter",
        "location": {"lat": lat, "lon": lon, "zone_id": zone, "county": "București", "label": f"Contor {asset}"},
        "target_date": D.isoformat(),
        "prediction": {
            "model_id": "a-lgbm",
            "model_version": "a-lgbm@fixture",
            "prediction_id": pid(),
            "label": label,
            "score": score,
            "interval_low": max(0.0, score - 0.18),
            "interval_high": min(1.0, score + 0.08),
            "confidence": "low" if abstain else ("high" if score > 0.8 else "medium"),
            "abstain": abstain,
            "abstain_reason": "doar 11 zile de istoric după montare" if abstain else None,
        },
        "impact": {
            "expected_value_lei": round(score * value, 2),
            "value_if_true_lei": value,
            "customers_affected": 1,
            "urgency_hours": 72,
            "safety_flag": label == "tamper",
            "assumptions_ref": "meters",
        },
        "effort": {"duration_min": 40, "crew_skill": "metering", "crew_size": 2, "requires_planned_outage": False},
        "explanation": {
            "top_factors": [
                {"feature": "zero_run_days_30d", "label_ro": "9 zile la rând cu consum zero", "value": 9, "contribution": 0.31},
                {"feature": "peer_ratio_post", "label_ro": "cu 72% sub vecinii de pe același post", "value": 0.28, "contribution": 0.22},
            ],
            "similar_cases": [{"case_id": "SGCC-0193", "outcome": "furt_confirmat", "similarity": 0.91}],
            "summary_ro": "Consum zero 9 zile după un istoric stabil și mult sub vecini. Merită verificat la fața locului.",
        },
        "data_quality": {"missing_ratio": 0.04, "input_issues": [], "synthetic": True, "data_sources": ["fixture ilustrativ"]},
        "recommended_action": "human_review" if abstain else ("inspect_on_site" if score > 0.6 else "remote_reading"),
        "created_at": NOW.isoformat(),
        "extra": {"series_ref": f"outputs/series/A/{asset}.json"},
    }


def wi_b(zone: str, county: str, lat: float, lon: float, score: float, customers: int) -> dict:
    value = round(customers * 0.06 * 12 * 2.5, 2)
    return {
        "work_item_id": f"B-{D:%Y%m%d}-{zone}",
        "source": "B",
        "kind": "storm_prepositioning",
        "asset_id": zone,
        "asset_type": "zone",
        "location": {"lat": lat, "lon": lon, "zone_id": zone, "county": county, "label": f"Zona {zone}"},
        "target_date": D.isoformat(),
        "time_window": {
            "start": datetime(2026, 11, 9, 12, 0, tzinfo=TZ).isoformat(),
            "end": datetime(2026, 11, 9, 20, 0, tzinfo=TZ).isoformat(),
        },
        "prediction": {
            "model_id": "b-lgbm-quantile",
            "model_version": "b-lgbm@fixture",
            "prediction_id": pid(),
            "label": "outage_risk",
            "score": score,
            "interval_low": max(0.0, score - 0.2),
            "interval_high": min(1.0, score + 0.1),
            "point_estimate": customers * 0.06,
            "point_unit": "clienți fără curent (vârf)",
            "point_interval": [customers * 0.01, customers * 0.15],
            "confidence": "medium",
        },
        "impact": {
            "expected_value_lei": round(score * value, 2),
            "value_if_true_lei": value,
            "customers_affected": int(customers * 0.06),
            "urgency_hours": 6,
            "safety_flag": False,
            "assumptions_ref": "storm",
        },
        "effort": {"duration_min": 480, "crew_skill": "mv_grid", "crew_size": 3, "requires_planned_outage": False},
        "explanation": {
            "top_factors": [
                {"feature": "wind_gust_max_kmh", "label_ro": "rafale de vânt de 85 km/h", "value": 85, "contribution": 0.41},
                {"feature": "precip_48h_mm", "label_ro": "32 mm de ploaie în 48 de ore", "value": 32, "contribution": 0.12},
            ],
            "similar_cases": [{"case_id": "EAGLEI-2019-06-OH-123", "outcome": "avarii_extinse", "similarity": 0.84}],
            "summary_ro": "Rafale de 85 km/h după-amiaza. În situații asemănătoare au căzut linii în mai multe localități.",
        },
        "data_quality": {"missing_ratio": 0.0, "input_issues": [], "synthetic": False, "data_sources": ["fixture ilustrativ"]},
        "recommended_action": "preposition_crew",
        "created_at": NOW.isoformat(),
    }


def wi_c(post: str, lat: float, lon: float, zone: str, score: float, vmax: float) -> dict:
    value = 820.0
    return {
        "work_item_id": f"C-{D:%Y%m%d}-{post}",
        "source": "C",
        "kind": "voltage_mitigation",
        "asset_id": post,
        "asset_type": "transformer_post",
        "location": {"lat": lat, "lon": lon, "zone_id": zone, "county": "Ilfov", "label": f"{post}, {zone}"},
        "target_date": D.isoformat(),
        "time_window": {
            "start": datetime(2026, 11, 9, 11, 0, tzinfo=TZ).isoformat(),
            "end": datetime(2026, 11, 9, 15, 0, tzinfo=TZ).isoformat(),
        },
        "prediction": {
            "model_id": "c-surrogate",
            "model_version": "c-lgbm@fixture",
            "prediction_id": pid(),
            "label": "overvoltage",
            "score": score,
            "point_estimate": vmax,
            "point_unit": "tensiune maximă (pu)",
            "point_interval": [round(vmax - 0.02, 3), round(vmax + 0.015, 3)],
            "confidence": "high" if score > 0.8 else "medium",
        },
        "impact": {
            "expected_value_lei": round(score * value, 2),
            "value_if_true_lei": value,
            "customers_affected": 38,
            "urgency_hours": 30,
            "safety_flag": False,
            "assumptions_ref": "voltage",
        },
        "effort": {"duration_min": 120, "crew_skill": "lv_grid", "crew_size": 3, "requires_planned_outage": True},
        "explanation": {
            "top_factors": [
                {"feature": "pv_kw_per_kva", "label_ro": "410 kW de panouri pe un transformator de 250 kVA", "value": 1.64, "contribution": 0.38},
                {"feature": "irradiance_noon_wm2", "label_ro": "soare puternic la prânz, 890 W/m²", "value": 890, "contribution": 0.27},
            ],
            "similar_cases": [],
            "summary_ro": "Mâine la prânz tensiunea poate urca la 1,12 față de limita de 1,10. Invertoarele s-ar opri singure.",
        },
        "data_quality": {"missing_ratio": 0.0, "input_issues": [], "synthetic": True, "data_sources": ["fixture ilustrativ"]},
        "recommended_action": "adjust_tap",
        "created_at": NOW.isoformat(),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    a = [
        wi_a("MTR-004217", 44.4321, 26.0254, "B-S6", 0.87, "tamper"),
        wi_a("MTR-019833", 44.4512, 26.1287, "B-S2", 0.64, "faulty"),
        wi_a("MTR-027710", 44.4080, 26.0901, "B-S5", 0.52, "faulty", abstain=True),
    ]
    b = [
        wi_b("CT-MEDGIDIA", "Constanța", 44.2500, 28.2731, 0.78, 21000),
        wi_b("IF-SNAGOV", "Ilfov", 44.7040, 26.1720, 0.41, 9000),
    ]
    c = [
        wi_c("PT-1432", 44.4285, 25.9905, "IF-CHIAJNA", 0.91, 1.12),
        wi_c("PT-0877", 44.5590, 26.0610, "IF-OTOPENI", 0.58, 1.095),
    ]
    for name, items in {"A": a, "B": b, "C": c}.items():
        for it in items:
            WorkItem.model_validate(it)
        (OUT / f"work_items_{name}.jsonl").write_text(
            "".join(json.dumps(it, ensure_ascii=False) + "\n" for it in items), encoding="utf-8"
        )

    bad = dict(a[0])
    bad = json.loads(json.dumps(bad))
    bad["work_item_id"] = "A-20261109-MTR-BAD"
    bad["location"]["lat"] = 51.5  # în afara României: intrare greșită
    bad["prediction"]["score"] = 1.4  # probabilitate imposibilă
    (OUT / "work_items_invalid.jsonl").write_text(json.dumps(bad, ensure_ascii=False) + "\n", encoding="utf-8")

    t0 = datetime(2026, 11, 9, 8, 0, tzinfo=TZ)
    audit = []
    decisions = []
    for rank, it in enumerate([a[0], c[0], a[1]], 1):
        aid = pid()
        decisions.append(
            Decision(
                work_item_id=it["work_item_id"],
                decision="assigned",
                reason_ro="Valoarea așteptată depășește costul vizitei și există capacitate.",
                rule_id="R-VALUE-OVER-COST",
                threshold={"min_net_value_lei": 0.0, "score_min": 0.5, "visit_cost_lei": 250.0},
                priority_score=round(it["impact"]["expected_value_lei"], 2),
                rank=rank,
                crew_id="E-BV-2" if it["source"] == "A" else "E-BV-3",
                audit_id=aid,
            )
        )
        audit.append(
            AuditRecord(
                audit_id=aid,
                ts=NOW,
                actor="agent",
                action="assigned",
                work_item_id=it["work_item_id"],
                prediction_id=it["prediction"]["prediction_id"],
                model_version=it["prediction"]["model_version"],
                rule_id="R-VALUE-OVER-COST",
                threshold={"min_net_value_lei": 0.0},
            )
        )
    aid = pid()
    decisions.append(
        Decision(
            work_item_id=a[2]["work_item_id"],
            decision="human_review",
            reason_ro="Modelul nu e sigur: prea puțin istoric. Decide un om.",
            rule_id="R-ABSTAIN",
            audit_id=aid,
        )
    )
    audit.append(AuditRecord(audit_id=aid, ts=NOW, actor="agent", action="human_review", work_item_id=a[2]["work_item_id"]))

    # Decizii pentru restul lucrărilor, câte una din fiecare tip
    def add(item_id: str, kind: str, reason: str, rule: str, threshold: dict | None = None, crew: str | None = None,
            rank: int | None = None, prio: float | None = None) -> None:
        aid = pid()
        decisions.append(Decision(work_item_id=item_id, decision=kind, reason_ro=reason, rule_id=rule,
                                  threshold=threshold or {}, crew_id=crew, rank=rank, priority_score=prio, audit_id=aid))
        audit.append(AuditRecord(audit_id=aid, ts=NOW, actor="agent", action=kind, work_item_id=item_id, rule_id=rule,
                                 threshold=threshold or {}))

    add(b[0]["work_item_id"], "assigned", "Risc mare de avarii între 12:00 și 20:00; echipa ajunge în zonă la 11:00.",
        "R-STORM-PREPOSITION", {"score_min": 0.6, "preposition_cost_lei": 2700.0}, crew="E-CT-1", rank=4,
        prio=round(b[0]["impact"]["expected_value_lei"], 2))
    add(b[1]["work_item_id"], "deferred", "Riscul e sub prag; zona rămâne urmărită.", "R-BELOW-THRESHOLD",
        {"score_min": 0.6})
    add(c[1]["work_item_id"], "notify", "Depășire probabilă, dar sub costul unei intervenții: mesaj către prosumatori.",
        "R-CHEAP-ACTION", {"score_min": 0.8, "tap_change_visit_cost_lei": 450.0})
    add("A-20261109-MTR-BAD", "rejected_invalid", "Intrare greșită: coordonate în afara României, scor peste 1.",
        "R-QUARANTINE")

    plan = Plan(
        plan_id="PLAN-fixture",
        plan_date=D,
        generated_at=NOW,
        planner_version="planner@fixture",
        scenario="fixture",
        summary=PlanSummary(
            items_in=8, items_valid=7, items_invalid=1, assigned=4, deferred=1, human_review=1, remote_actions=0,
            notifications=1, crews_used=3, expected_value_lei=round(sum(
                it["impact"]["expected_value_lei"] for it in (a[0], a[1], c[0], b[0])), 2), total_km=0.0,
        ),
        routes=[
            Route(
                crew_id="E-BV-2", depot_id="D-BUC-V", depart_at=t0, return_at=t0 + timedelta(minutes=175),
                stops=[
                    Stop(seq=1, work_item_id=a[0]["work_item_id"], eta=t0 + timedelta(minutes=25), duration_min=40, travel_km=6.1),
                    Stop(seq=2, work_item_id=a[1]["work_item_id"], eta=t0 + timedelta(minutes=110), duration_min=40, travel_km=11.8),
                ],
                total_km=29.0, total_work_min=80, total_travel_min=95,
            ),
            Route(
                crew_id="E-BV-3", depot_id="D-BUC-V", depart_at=t0 + timedelta(hours=2, minutes=53),
                return_at=t0 + timedelta(hours=5, minutes=7),
                stops=[Stop(seq=1, work_item_id=c[0]["work_item_id"], eta=t0 + timedelta(hours=3), duration_min=120, travel_km=2.4)],
                total_km=4.8, total_work_min=120, total_travel_min=14,
            ),
        ],
        decisions=decisions,
        alerts=[
            Alert(
                alert_id="AL-1", severity="warning", title_ro="Risc de avarii în zona Medgidia",
                body_ro="Rafale de 85 km/h între 12:00 și 20:00. Recomand o echipă în zonă de la 11:00.",
                work_item_ids=[b[0]["work_item_id"]], channel="dispecerat", created_at=NOW,
            )
        ],
        notifications=[
            Notification(
                notification_id="N-1", audience="prosumatori", asset_id="PT-1432",
                message_ro="Mâine între 11 și 15 e soare puternic. Dacă puteți, porniți atunci mașina de spălat și boilerul.",
                scheduled_for=datetime(2026, 11, 8, 18, 0, tzinfo=TZ), work_item_id=c[0]["work_item_id"],
            )
        ],
        sources_status={"A": "ok", "B": "ok", "C": "ok"},
    )
    plan.routes.append(Route(
        crew_id="E-CT-1", depot_id="D-CTA", depart_at=datetime(2026, 11, 9, 10, 15, tzinfo=TZ),
        return_at=datetime(2026, 11, 9, 20, 45, tzinfo=TZ),
        stops=[Stop(seq=1, work_item_id=b[0]["work_item_id"], eta=datetime(2026, 11, 9, 11, 0, tzinfo=TZ),
                    duration_min=480, travel_km=36.2)],
        total_km=72.4, total_work_min=480, total_travel_min=90,
    ))
    plan.summary.total_km = round(sum(r.total_km for r in plan.routes), 1)
    Plan.model_validate(plan.model_dump())

    # Serii ilustrative pentru graficele din detaliul lucrării
    import math
    days = [D - timedelta(days=59 - i) for i in range(60)]
    pts_a = []
    for i, d in enumerate(days):
        normal = round(7.5 + 1.8 * math.sin(i / 7 * 2 * math.pi), 2)
        zero = i >= 51
        pts_a.append(SeriesPoint(t=d, value=0.0 if zero else round(normal * (0.95 + 0.1 * ((i * 37) % 10) / 10), 2),
                                 expected=normal, flag="zero" if zero else None))
    hours = [datetime(2026, 11, 9, 0, 0, tzinfo=TZ) + timedelta(hours=h) for h in range(48)]
    pts_b = []
    for h, t in enumerate(hours):
        gust = round(25 + 60 * math.exp(-((h - 15) ** 2) / 18), 1)
        pts_b.append(SeriesPoint(t=t, value=gust, expected=round(min(0.95, gust / 100), 3)))
    quarter = [datetime(2026, 11, 9, 0, 0, tzinfo=TZ) + timedelta(minutes=15 * q) for q in range(96)]
    pts_c = []
    for q, t in enumerate(quarter):
        sun = max(0.0, math.sin((q - 28) / 56 * math.pi)) if 28 <= q <= 84 else 0.0
        p50 = round(1.02 + 0.10 * sun, 3)
        pts_c.append(SeriesPoint(t=t, value=None, expected=p50, low=round(p50 - 0.02 * sun - 0.005, 3),
                                 high=round(p50 + 0.015 * sun + 0.005, 3),
                                 flag="peste_limita" if p50 > 1.10 else None))
    series = [
        Series(work_item_id=a[0]["work_item_id"], source="A", title_ro="Consum zilnic, ultimele 60 de zile", unit="kWh",
               points=pts_a, annotations=[SeriesAnnotation(t=days[51], label_ro="începe consumul zero")], synthetic=True),
        Series(work_item_id=b[0]["work_item_id"], source="B", title_ro="Rafale de vânt și riscul de avarii, 48 de ore",
               unit="km/h", points=pts_b, thresholds={"rafala_prag_kmh": 70.0},
               annotations=[SeriesAnnotation(t=hours[12], label_ro="începe fereastra de risc")], synthetic=True),
        Series(work_item_id=c[0]["work_item_id"], source="C", title_ro="Tensiunea maximă la post, la 15 minute",
               unit="pu", points=pts_c, thresholds={"limita_tensiune_pu": 1.10}, synthetic=True),
    ]
    for sr in series:
        (OUT / f"series_{sr.work_item_id}.json").write_text(sr.model_dump_json(indent=2) + "\n", encoding="utf-8")

    (OUT / "plan_example.json").write_text(plan.model_dump_json(indent=2) + "\n", encoding="utf-8")
    (OUT / "audit_example.jsonl").write_text("".join(r.model_dump_json() + "\n" for r in audit), encoding="utf-8")
    print(f"Fixture-uri scrise în {OUT}")


if __name__ == "__main__":
    main()
