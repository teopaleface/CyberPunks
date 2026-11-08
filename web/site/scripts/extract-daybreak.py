"""Extract the numbers the site shows from the team's demo snapshot.

Usage (from web/):
    python -I scripts/extract-daybreak.py <path to CyberPunks/outputs/demo> src/data/daybreak.json

Everything on the site comes from this file, which comes from the planner's
real run (`outputs/demo/`, branch `design` of teopaleface/CyberPunks).
Nothing is invented here: we only select, round and translate labels.
"""

import collections
import json
import sys
from pathlib import Path

demo = Path(sys.argv[1])
out = Path(sys.argv[2])
reports = Path(sys.argv[3]) if len(sys.argv) > 3 else demo.parent.parent / "reports"
plan_dir = demo / "plans" / "demo-vara"


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


plan = load(plan_dir / "plan.json")
posts = load(plan_dir / "posts.json")
alerts = load(plan_dir / "alerts.json")
notifications = load(plan_dir / "notifications.json")
items = {}
with open(plan_dir / "work_items.jsonl", encoding="utf-8") as f:
    for line in f:
        w = json.loads(line)
        items[w["work_item_id"]] = w
decisions = {d["work_item_id"]: d for d in plan["decisions"]}

DIAG = {
    "contor_client": "Contor defect la un client",
    "furt_inainte_contor": "Furt înainte de contor",
    "pierdere_tehnica": "Pierdere tehnică (cablu, faze)",
    "client_post_gresit": "Client la postul greșit",
    "contor_bilant_setat": "Contorul de post setat greșit",
    "normal": "În regulă",
}
DECISION = {
    "assigned": "Echipă trimisă",
    "remote_action": "Verificare de la distanță",
    "human_review": "Decide un om",
    "deferred": "Amânat",
    "notify": "Notificare",
}


def r(x, n=0):
    return None if x is None else round(x, n) if n else round(x)


# ---- posts (map + balance) ----
post_rows = []
for p in posts:
    post_rows.append(
        {
            "id": p["post_id"],
            "label": p["label"],
            "lat": r(p["lat"], 5),
            "lng": r(p["lon"], 5),
            "zone": p["zone_id"],
            "lossLeiMonth": r(p["loss_lei_month"]),
            "diagnosis": p["diagnosis"],
            "color": p["color"],
            "score": r(p["bilant_score"], 3),
            "decision": p["bilant_decision"],
            "metersFlagged": p["meters_flagged"],
            "voltageP90": r(p["voltage_p90_pu"], 3),
            "kva": p["kva"],
            "workItem": p["bilant_work_item_id"],
        }
    )


# ---- balance cases: the real bilanț work items, with factors ----
post_loss = {p["post_id"]: p["loss_lei_month"] for p in posts}
def case(wid):
    w = items[wid]
    d = decisions.get(wid, {})
    pred = w["prediction"]
    ex = w.get("extra") or {}
    th = d.get("threshold") or {}
    return {
        "id": wid,
        "post": w["asset_id"],
        "label": w["location"]["label"],
        "county": w["location"].get("county"),
        "lat": w["location"]["lat"],
        "lng": w["location"]["lon"],
        "diagnosis": pred["label"],
        "diagnosisRo": DIAG.get(pred["label"], pred["label"]),
        "score": r(pred["score"], 3),
        "excessKwhDay": r(pred.get("point_estimate"), 1),
        "lossLeiMonth": r(post_loss.get(w["asset_id"])),
        "expectedValueLei": r(w["impact"]["expected_value_lei"]),
        "customers": w["impact"]["customers_affected"],
        "decision": d.get("decision"),
        "decisionRo": DECISION.get(d.get("decision"), d.get("decision")),
        "rule": d.get("rule_id"),
        "reason": d.get("reason_ro"),
        "crew": d.get("crew_id"),
        "factors": [
            {"label": f["label_ro"], "contribution": r(f["contribution"], 2)}
            for f in (w.get("explanation") or {}).get("top_factors", [])[:4]
        ],
        "proba": {k: r(v, 3) for k, v in (ex.get("diagnosis_proba") or {}).items()},
        "suspectMeter": ex.get("suspect_meter"),
        "model": pred.get("model_version"),
        "predictionId": pred.get("prediction_id"),
    }


bilant_ids = [p["bilant_work_item_id"] for p in posts if p["bilant_work_item_id"] and p["diagnosis"]]
by_diag = collections.defaultdict(list)
for wid in bilant_ids:
    if wid in items:
        by_diag[items[wid]["prediction"]["label"]].append(wid)
picked = []
# one strong case per diagnosis, then the next biggest losses
for diag in ["contor_client", "furt_inainte_contor", "pierdere_tehnica", "client_post_gresit", "contor_bilant_setat"]:
    ids = sorted(by_diag.get(diag, []), key=lambda i: -items[i]["impact"]["expected_value_lei"])
    picked += ids[:1]
rest = sorted(
    (i for i in bilant_ids if i in items and i not in picked),
    key=lambda i: -items[i]["impact"]["expected_value_lei"],
)
picked += rest[: 8 - len(picked)]
cases = [case(i) for i in picked]

# ---- ranking: biggest expected value across all sources, with decisions ----
ranked = sorted(plan["decisions"], key=lambda d: -(items[d["work_item_id"]]["impact"]["expected_value_lei"] or 0))
ranking = []
for d in ranked[:10]:
    w = items[d["work_item_id"]]
    ranking.append(
        {
            "id": d["work_item_id"],
            "source": w["source"],
            "label": w["location"]["label"],
            "kind": w["kind"],
            "expectedValueLei": r(w["impact"]["expected_value_lei"]),
            "score": r(w["prediction"]["score"], 2),
            "decision": d["decision"],
            "decisionRo": DECISION.get(d["decision"], d["decision"]),
            "rule": d.get("rule_id"),
            "reason": d.get("reason_ro"),
            "crew": d.get("crew_id"),
        }
    )

# ---- human review queue ----
queue = []
for d in plan["decisions"]:
    if d["decision"] == "human_review" and len(queue) < 8:
        w = items[d["work_item_id"]]
        queue.append(
            {
                "id": d["work_item_id"],
                "source": w["source"],
                "label": w["location"]["label"],
                "score": r(w["prediction"]["score"], 2),
                "low": r(w["prediction"].get("interval_low"), 2),
                "high": r(w["prediction"].get("interval_high"), 2),
                "reason": d.get("reason_ro"),
                "expectedValueLei": r(w["impact"]["expected_value_lei"]),
            }
        )

# ---- routes ----
routes = []
for rt in plan["routes"]:
    routes.append(
        {
            "crew": rt["crew_id"],
            "depot": rt["depot_id"],
            "depart": rt["depart_at"][11:16],
            "back": (rt.get("return_at") or "")[11:16],
            "stops": len(rt["stops"]),
            "km": r(sum(s.get("travel_km") or 0 for s in rt["stops"]), 1),
            "sources": dict(collections.Counter(s["work_item_id"][0] for s in rt["stops"])),
        }
    )

# ---- per source ----
per_source = collections.defaultdict(lambda: collections.Counter())
for d in plan["decisions"]:
    per_source[d["work_item_id"][0]][d["decision"]] += 1
    per_source[d["work_item_id"][0]]["total"] += 1

# ---- models and agent evaluation ----
def report_path(k, name):
    current = reports / k / name
    return current if current.exists() else demo / "reports" / k / name


def metrics(k):
    m = load(report_path(k, "metrics.json"))
    return m.get("metrics", {}), m.get("model_version"), m.get("baseline") or m.get("baselines")


mA, vA, _ = metrics("A")
mB, vB, _ = metrics("B")
mC, vC, _ = metrics("C")
mBil, vBil, _ = metrics("bilant")
ev = load(report_path("planner", "agent_eval.json"))
strategies = ev["main"]["strategies"]
NAMES = {
    "agent": "Agentul (reguli + OR-Tools)",
    "top_k_scor": "Top-K după scor",
    "primul_venit": "Primul venit",
    "aleator": "Aleator",
    "doar_contoare": "Doar contoare (o sursă)",
}
evaluation = [
    {
        "key": k,
        "name": NAMES.get(k, k),
        "netLeiDay": r(v.get("net_value_lei_per_day")),
        "kmDay": r(v.get("km_per_day")),
        "uselessRate": r(v.get("useless_visit_rate"), 3),
        "urgentMissedRate": r(v.get("urgent_missed_rate"), 3),
        "stormsCovered": v.get("storms_covered_total"),
        "stormsTotal": v.get("storms_true_total"),
    }
    for k, v in strategies.items()
]

# ---- work items in full, for the item pages (explainability) ----
series_dir = demo / "series" / "demo-vara"


def series_of(wid):
    p = series_dir / f"{wid}.json"
    if not p.exists():
        return None
    sr = load(p)
    return {
        "title": sr["title_ro"],
        "unit": sr["unit"],
        "points": [[pt["t"][:16], pt.get("value"), pt.get("expected"), pt.get("low"), pt.get("high")] for pt in sr["points"]],
        "thresholds": sr.get("thresholds") or {},
        "annotations": [{"t": a["t"][:16], "label": a["label_ro"]} for a in (sr.get("annotations") or [])],
        "synthetic": sr.get("synthetic"),
    }


def full_item(wid):
    w = items[wid]
    d = decisions.get(wid, {})
    pred = w["prediction"]
    ex = w.get("explanation") or {}
    dq = w.get("data_quality") or {}
    return {
        "id": wid,
        "source": w["source"],
        "kind": w["kind"],
        "label": w["location"]["label"],
        "county": w["location"].get("county"),
        "lat": w["location"]["lat"],
        "lng": w["location"]["lon"],
        "prediction": {
            "model": pred.get("model_version"),
            "id": pred.get("prediction_id"),
            "label": pred.get("label"),
            "score": r(pred.get("score"), 3),
            "low": r(pred.get("interval_low"), 3),
            "high": r(pred.get("interval_high"), 3),
            "point": pred.get("point_estimate"),
            "pointUnit": pred.get("point_unit"),
            "pointInterval": pred.get("point_interval"),
            "confidence": pred.get("confidence"),
            "abstain": pred.get("abstain"),
            "abstainReason": pred.get("abstain_reason"),
        },
        "impact": {
            "expectedValueLei": r(w["impact"].get("expected_value_lei")),
            "valueIfTrueLei": r(w["impact"].get("value_if_true_lei")),
            "customers": w["impact"].get("customers_affected"),
            "urgencyHours": w["impact"].get("urgency_hours"),
            "safety": w["impact"].get("safety_flag"),
        },
        "effort": w.get("effort"),
        "summary": ex.get("summary_ro"),
        "factors": [{"label": f["label_ro"], "contribution": r(f["contribution"], 2)} for f in ex.get("top_factors", [])[:5]],
        "similar": [
            {"id": c.get("case_id"), "outcome": c.get("outcome"), "similarity": c.get("similarity"), "note": c.get("note_ro")}
            for c in ex.get("similar_cases", [])[:3]
        ],
        "quality": {"synthetic": dq.get("synthetic"), "issues": dq.get("input_issues", []), "sources": dq.get("data_sources", [])},
        "action": w.get("recommended_action"),
        "decision": d.get("decision"),
        "decisionRo": DECISION.get(d.get("decision"), d.get("decision")),
        "rule": d.get("rule_id"),
        "threshold": d.get("threshold") or {},
        "reason": d.get("reason_ro"),
        "crew": d.get("crew_id"),
        "auditId": d.get("audit_id"),
        "series": series_of(wid),
    }


chosen = []


def add(wid):
    if wid in items and wid not in chosen:
        chosen.append(wid)


for d in plan["decisions"]:
    if d["decision"] == "human_review":
        add(d["work_item_id"])
for c in cases:
    add(c["id"])
for src in "ABC":
    src_dec = [x for x in plan["decisions"] if x["work_item_id"][0] == src]
    for d in sorted(src_dec, key=lambda x: -(items[x["work_item_id"]]["impact"]["expected_value_lei"] or 0))[:14]:
        add(d["work_item_id"])
for rt in plan["routes"]:
    for st in rt["stops"][:2]:
        add(st["work_item_id"])
full_items = [full_item(i) for i in chosen]

# every routed stop, with its position, for the map
route_stops = []
for rt in plan["routes"]:
    for st in rt["stops"]:
        w = items.get(st["work_item_id"])
        if not w:
            continue
        route_stops.append({
            "crew": rt["crew_id"], "seq": st["seq"], "id": st["work_item_id"], "eta": st["eta"][11:16],
            "lat": w["location"]["lat"], "lng": w["location"]["lon"], "source": w["source"],
            "label": w["location"]["label"], "km": st.get("travel_km"),
        })

# every work item, compact: id, source, lat, lng, decision, value, score
all_items = []
for wid, w in items.items():
    d = decisions.get(wid, {})
    all_items.append([wid, w["source"], round(w["location"]["lat"], 4), round(w["location"]["lon"], 4),
                      d.get("decision"), r(w["impact"].get("expected_value_lei")), r(w["prediction"].get("score"), 2)])

# ---- journal sample ----
audit_rows = []
audit_counts = collections.Counter()
seen = collections.Counter()
with open(plan_dir / "audit.jsonl", encoding="utf-8") as f:
    for line in f:
        a = json.loads(line)
        audit_counts[f"{a['actor']}:{a['action']}"] += 1
        if seen[a["action"]] >= 6:
            continue
        seen[a["action"]] += 1
        audit_rows.append({
            "id": a["audit_id"], "ts": a["ts"][:16], "actor": a["actor"], "action": a["action"],
            "workItem": a.get("work_item_id"), "prediction": a.get("prediction_id"), "model": a.get("model_version"),
            "rule": a.get("rule_id"), "note": a.get("note"),
        })
audit_counts = dict(audit_counts)


def model_card(k):
    m = load(report_path(k, "metrics.json"))
    return {
        "id": m.get("model_id"), "version": m.get("model_version"), "task": m.get("task"), "dataset": m.get("dataset"),
        "split": m.get("split"), "testSize": m.get("test_size"), "primary": m.get("primary_metric"),
        "metrics": m.get("metrics"), "baselineId": m.get("baseline_id"), "baseline": m.get("baseline_metrics"),
        "syntheticShare": m.get("synthetic_share"), "reproduce": m.get("reproduce_cmd"),
    }


robust = ev.get("robustness_overconfident_model", {})
ablations = [
    {"key": k, "label": v.get("label_ro", k), "netLeiDay": r(v.get("net_value_lei_per_day")),
     "uselessRate": r(v.get("useless_visit_rate"), 3), "urgentMissedRate": r(v.get("urgent_missed_rate"), 3)}
    for k, v in (ev.get("ablations") or {}).items()
]

# ---- crews (config/crews.yaml, next to outputs/), parsed without a YAML library ----
import re

DEPOT_RO = {
    "D-BUC-V": "București Vest", "D-BUC-E": "București Est", "D-CTA": "Constanța", "D-TM": "Timișoara",
    "D-ARD": "Arad", "D-RES": "Reșița", "D-DEV": "Deva",
}
crews = []
crews_file = demo.parent.parent / "config" / "crews.yaml"
if crews_file.exists():
    for m in re.finditer(r'crew_id:\s*"([^"]+)",\s*depot_id:\s*"([^"]+)",\s*skills:\s*\[([^\]]*)\],\s*size:\s*(\d+)',
                         crews_file.read_text(encoding="utf-8")):
        cid, depot, skills, size = m.groups()
        crews.append({"id": cid, "depot": depot, "depotRo": DEPOT_RO.get(depot, depot),
                      "skills": [s.strip() for s in skills.split(",") if s.strip()], "size": int(size)})
shift = {"start": "08:00", "end": "16:00"}

data = {
    "source": "CyberPunks outputs/demo, fixed summer-demo plan; model evaluation reports are versioned separately",
    "planId": plan["plan_id"],
    "planDate": plan["plan_date"],
    "generatedAt": plan["generated_at"],
    "plannerVersion": plan["planner_version"],
    "summary": plan["summary"],
    "decisionCounts": dict(collections.Counter(d["decision"] for d in plan["decisions"])),
    "perSource": {k: dict(v) for k, v in per_source.items()},
    "posts": post_rows,
    "cases": cases,
    "ranking": ranking,
    "queue": queue,
    "routes": routes,
    "alerts": [
        {"id": a["alert_id"], "severity": a.get("severity"), "title": a.get("title_ro"), "body": a.get("body_ro")}
        for a in alerts
    ],
    "notifications": [
        {"id": n["notification_id"], "audience": n.get("audience"), "message": n.get("message_ro")}
        for n in notifications[:6]
    ],
    "models": {
        "A": {"version": vA, "rocAuc": mA.get("roc_auc"), "prAuc": mA.get("pr_auc"), "precisionAtK": mA.get("precision_at_k"),
               "sgccRocAuc": mA.get("sgcc_roc_auc"), "iforestRocAuc": mA.get("iforest_roc_auc")},
        "B": {"version": vB, **{k: mB[k] for k in list(mB)[:8]}},
        "C": {"version": vC, **{k: mC[k] for k in list(mC)[:8]}},
        "bilant": {"version": vBil, "diagnosisAccuracy": mBil.get("diagnoza_accuracy"), "diagnosisMacroF1": mBil.get("diagnoza_macro_f1"),
                    "normalMaeKwhDay": mBil.get("normal_mae_kwh_day"), "fixedPctMaeKwhDay": mBil.get("procent_fix_mae_kwh_day"),
                    "coverageP10P90": mBil.get("normal_coverage_p10_p90"), "testPosts": mBil.get("normal_test_posts")},
    },
    "evaluation": {
        "days": ev["main"]["days"],
        "synthetic": ev.get("synthetic", True),
        "rows": evaluation,
        "reproduce": ev.get("reproduce_cmd"),
        "robust": {
            "days": robust.get("days"),
            "rows": [
                {"key": k, "name": NAMES.get(k, k), "netLeiDay": r(v.get("net_value_lei_per_day")),
                 "urgentMissedRate": r(v.get("urgent_missed_rate"), 3)}
                for k, v in (robust.get("strategies") or {}).items()
            ],
        },
        "ablations": ablations,
    },
    "items": full_items,
    "allItems": all_items,
    "routeStops": route_stops,
    "audit": audit_rows,
    "auditCounts": audit_counts,
    "modelCards": {k: model_card(k) for k in ["A", "B", "C", "bilant"]},
    "crews": crews,
    "shift": shift,
}

out.parent.mkdir(parents=True, exist_ok=True)
serialized = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
if not out.exists() or out.read_text(encoding="utf-8") != serialized:
    out.write_text(serialized, encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")
print("wrote", out, round(out.stat().st_size / 1024), "KiB")
print("cases", [(c["post"], c["diagnosis"], c["lossLeiMonth"], c["decision"]) for c in cases])
print("ranking", [(x["id"], x["expectedValueLei"], x["decision"]) for x in ranking[:5]])
print("models B keys", list(mB)[:8]); print("models C keys", list(mC)[:8])
print("eval", [(e["key"], e["netLeiDay"]) for e in evaluation])
