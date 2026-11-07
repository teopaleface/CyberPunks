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
                threshold={"min_net_value_lei": 0.0, "score_min": 0.5},
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

    plan = Plan(
        plan_id="PLAN-fixture",
        plan_date=D,
        generated_at=NOW,
        planner_version="planner@fixture",
        scenario="fixture",
        summary=PlanSummary(
            items_in=8, items_valid=7, items_invalid=1, assigned=3, deferred=1, human_review=1, remote_actions=0,
            notifications=1, crews_used=2, expected_value_lei=2741.2, total_km=31.4,
        ),
        routes=[
            Route(
                crew_id="E-BV-2", depot_id="D-BUC-V",
                stops=[
                    Stop(seq=1, work_item_id=a[0]["work_item_id"], eta=t0 + timedelta(minutes=25), duration_min=40, travel_km=6.1),
                    Stop(seq=2, work_item_id=a[1]["work_item_id"], eta=t0 + timedelta(minutes=110), duration_min=40, travel_km=11.8),
                ],
                total_km=29.0, total_work_min=80, total_travel_min=95,
            ),
            Route(
                crew_id="E-BV-3", depot_id="D-BUC-V",
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
    (OUT / "plan_example.json").write_text(plan.model_dump_json(indent=2) + "\n", encoding="utf-8")
    (OUT / "audit_example.jsonl").write_text("".join(r.model_dump_json() + "\n" for r in audit), encoding="utf-8")
    print(f"Fixture-uri scrise în {OUT}")


if __name__ == "__main__":
    main()
