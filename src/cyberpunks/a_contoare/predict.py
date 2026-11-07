"""Lucrările firului A pentru planificator: contoarele de verificat mâine, cu motivul și valoarea.

    uv run python -m cyberpunks.a_contoare.predict --scenario demo-vara            # data din config/scenarios.yaml
    uv run python -m cyberpunks.a_contoare.predict --scenario maine --date 2026-11-08

Din cod (planificatorul):  `from cyberpunks.a_contoare.predict import run; run("demo-vara", None) -> Path`

Pașii (Perceive -> Estimate -> recomandare; decizia finală o ia planificatorul):
1. populația demo: 10.000 de contoare SINTETICE în București-Ilfov, cu profile reale din Londra (demo.py);
2. validarea intrărilor: Wh în loc de kWh, valori imposibile, istoric prea scurt (validate.py);
3. features zilnice și la 30 de minute, comparația cu vecinii de pe același post;
4. modelul `a-lgbm`: scor calibrat de problemă, interval Venn-ABERS, decizie conformal, tipul probabil;
5. alegerea lucrărilor: cele sigure ("problemă" după conformal) după valoarea așteptată, cele nesigure la om;
6. explicația (SHAP, cazuri similare), valoarea în lei din config/economics.yaml, seria pentru grafic.

Scrie: outputs/work_items/<s>/A.jsonl (WorkItem), outputs/series/<s>/<id>.json (Series),
outputs/work_items/<s>/A_summary.json (cifrele zilei), outputs/work_items/<s>/A_ground_truth.csv
(ce am injectat, DOAR pentru evaluarea agentului; deciziile nu îl folosesc).
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from cyberpunks.a_contoare.baselines import rule_score
from cyberpunks.a_contoare.demo import build_population, load_topology, target_date_from_scenario
from cyberpunks.a_contoare.explain import SimilarCases, top_factors
from cyberpunks.a_contoare.features import daily_features, intraday_features
from cyberpunks.a_contoare.lcl import INTRADAY_BASE, RECENT, build_samples, daily_from_halfhours, economics
from cyberpunks.a_contoare.model import MeterModel
from cyberpunks.a_contoare.train import SIMILAR_REF
from cyberpunks.a_contoare.validate import check_window
from cyberpunks.common.contracts import Series, WorkItem
from cyberpunks.common.paths import OUTPUTS, work_items_path

TZ = ZoneInfo("Europe/Bucharest")
MAX_ACTION = 150  # lucrări sigure trimise planificatorului (cele mai valoroase)
MAX_WATCHLIST = 40  # următoarele, de urmărit fără vizită
MAX_REVIEW = 40  # cazuri "nu sunt sigur" trimise la om
MIN_REVIEW_SCORE = 0.10  # sub acest scor, un caz nesigur nu merită timpul unui om
SERIES_DAYS = 60
LOW_LEVEL_QUANTILE = 0.20  # chintila de jos a consumului: furtul suspectat merge întâi la om (etică)
DATA_SOURCES = [
    "Low Carbon London (UK Power Networks, CC BY 4.0): profile reale de consum la 30 de minute",
    "defecte și furturi injectate de echipă (date sintetice)",
    "topologie sintetică București-Ilfov pe OpenStreetMap (ODbL)",
]
ACTION_RO = {
    "inspect_on_site": "verificare la fața locului",
    "remote_reading": "citire la distanță, apoi vizită dacă se confirmă",
    "watchlist": "urmărire, fără vizită deocamdată",
    "human_review": "decide un om",
}
LABEL_RO = {"faulty": "contor probabil defect", "tamper": "posibilă intervenție la contor"}


def _confidence(score: float, decision: str) -> str:
    if decision == "problem" and score >= 0.6:
        return "high"
    if score >= 0.3:
        return "medium"
    return "low"


def _post_peers(daily: np.ndarray, post_ids: np.ndarray) -> np.ndarray:
    """Mediana zilnică a vecinilor de pe același post, pentru fiecare contor (forma lui `daily`)."""
    peer = np.empty_like(daily)
    for p in np.unique(post_ids):
        m = post_ids == p
        with np.errstate(all="ignore"):
            med = np.nanmedian(daily[m], axis=0)
        peer[m] = med
    return peer


def _expected_band(x: np.ndarray, peer: np.ndarray, recent: int = RECENT) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Ce ar fi fost normal: nivelul propriu din istoric, mutat după sezonul vecinilor (P10, P50, P90)."""
    base_x, base_p = x[:-recent], peer[:-recent]
    with np.errstate(all="ignore"):
        ratio = base_x / np.where(base_p > 1e-6, base_p, np.nan)
    ratio = ratio[np.isfinite(ratio)]
    if ratio.size < 10:
        lvl = np.nanmedian(base_x) if np.isfinite(base_x).any() else np.nan
        return np.full_like(x, lvl), np.full_like(x, np.nan), np.full_like(x, np.nan)
    q10, q50, q90 = np.quantile(ratio, [0.1, 0.5, 0.9])
    return peer * q50, peer * q10, peer * q90


def _deficit_kwh_day(x: np.ndarray, expected: np.ndarray, recent: int = RECENT) -> float:
    """kWh pe zi lipsă în ultimele 4 săptămâni, față de ce ar fi fost normal (0 dacă nu lipsește nimic)."""
    obs, exp = x[-recent:], expected[-recent:]
    m = np.isfinite(obs) & np.isfinite(exp)
    if m.sum() < 5:
        return 0.0
    return float(max(0.0, np.median(exp[m]) - np.median(obs[m])))


def _trailing_gap(x: np.ndarray) -> int:
    n = 0
    for v in x[::-1]:
        if np.isfinite(v):
            break
        n += 1
    return n


def _flags(x: np.ndarray, expected: np.ndarray) -> list[str | None]:
    out: list[str | None] = []
    med = np.nanmedian(x[np.isfinite(x) & (x > 0)]) if np.isfinite(x).any() else 1.0
    prev = None
    for v, e in zip(x, expected, strict=True):
        if not np.isfinite(v):
            f = "gol"
        elif v < 0:
            f = "negativ"
        elif v == 0:
            f = "zero"
        elif v > max(5 * (e if np.isfinite(e) else med), 3 * med) and v > 2:
            f = "salt"
        elif prev is not None and v == prev:
            f = "plat"
        else:
            f = None
        prev = v if np.isfinite(v) else prev
        out.append(f)
    return out


def _annotations(days: pd.DatetimeIndex, x: np.ndarray, expected: np.ndarray, flags: list[str | None]) -> list[dict]:
    notes = []
    for flag, text in (("zero", "începe consumul zero"), ("gol", "încep lipsurile de date"),
                       ("plat", "începe valoarea repetată"), ("negativ", "apar citiri negative")):
        idx = [i for i, f in enumerate(flags) if f == flag]
        if len(idx) >= 2:
            notes.append({"t": days[idx[0]].date().isoformat(), "label_ro": text})
    if not notes:
        with np.errstate(all="ignore"):
            r = pd.Series(x / np.where(expected > 1e-6, expected, np.nan)).rolling(7, min_periods=4).median()
        low = np.flatnonzero((r < 0.7).to_numpy())
        if low.size:
            notes.append({"t": days[max(0, low[0] - 6)].date().isoformat(), "label_ro": "consumul scade sub normal"})
    return notes[:3]


def _series(work_item_id: str, meter_id: str, days: pd.DatetimeIndex, x: np.ndarray, peer: np.ndarray) -> dict:
    exp, low, high = _expected_band(x, peer)
    sl = slice(len(x) - SERIES_DAYS, len(x))
    d, xv, ev, lv, hv = days[sl], x[sl], exp[sl], low[sl], high[sl]
    flags = _flags(xv, ev)

    def num(v: float) -> float | None:
        return round(float(v), 3) if np.isfinite(v) else None

    points = [
        {"t": t.date().isoformat(), "value": num(a), "expected": num(b), "low": num(c), "high": num(e), "flag": f}
        for t, a, b, c, e, f in zip(d, xv, ev, lv, hv, flags, strict=True)
    ]
    return {
        "contract_version": "1.0",
        "work_item_id": work_item_id,
        "source": "A",
        "title_ro": f"Consum zilnic, contor {meter_id}, ultimele {SERIES_DAYS} de zile (date sintetice)",
        "unit": "kWh",
        "points": points,
        "thresholds": {},
        "annotations": _annotations(d, xv, ev, flags),
        "synthetic": True,
    }


def score_population(target: date, scenario: str) -> tuple[pd.DataFrame, pd.DataFrame, np.ndarray, np.ndarray, object]:
    """Scorează toate contoarele demo. Întoarce (tabel contoare + predicții, features, zilnic, vecini, populația)."""
    pop = build_population(target, scenario)
    model = MeterModel.load("a-lgbm")
    checks = [check_window(pop.hh[i]) for i in range(len(pop.meters))]
    hh = np.stack([c.hh for c in checks]).astype(np.float64)
    daily = daily_from_halfhours(hh)
    post_ids = pop.meters["post_id"].to_numpy()
    peer = _post_peers(daily, post_ids)
    feats = pd.concat(
        [
            daily_features(daily, peer),
            intraday_features(hh[:, -RECENT:], hh[:, -RECENT - INTRADAY_BASE : -RECENT]),
        ],
        axis=1,
    )
    pred = model.predict(feats)
    tab = pop.meters.copy()
    tab["issues"] = [c.issues for c in checks]
    tab["data_abstain"] = [c.abstain_reason for c in checks]
    tab["rule_score"] = rule_score(feats)
    tab = pd.concat([tab, pred], axis=1)
    tab.attrs["model_version"] = model.version
    tab.attrs["source_date"] = str(pop.source_date.date())
    return tab, feats, daily, peer, (pop, model)


def run(scenario: str, date: str | None = None) -> Path:
    """Scrie lucrările A pentru `scenario` la data `date` (sau cea din config) și întoarce calea fișierului JSONL."""
    np.seterr(all="ignore")
    target = target_date_from_scenario(scenario, date)
    tab, feats, daily, peer, (pop, model) = score_population(target, scenario)
    econ = economics()
    now = datetime.now(TZ).replace(microsecond=0)
    _meters, posts = load_topology()
    post_label = dict(zip(posts["post_id"], posts["label"], strict=True))
    low_level_cut = float(np.nanquantile(feats["level_kwh"], LOW_LEVEL_QUANTILE))

    # valoarea estimată (în lei) pentru fiecare contor: kWh lipsă pe zi × orizont × cost (+ componenta fixă la defect)
    deficits, expected_series = [], []
    for i in range(len(tab)):
        exp, _, _ = _expected_band(daily[i], peer[i])
        expected_series.append(exp)
        deficits.append(_deficit_kwh_day(daily[i], exp))
    tab["deficit_kwh_day"] = np.round(deficits, 3)
    fixed = np.where(tab["label"] == "faulty", econ["faulty_fixed_lei"], 0.0)
    tab["value_if_true"] = np.round(tab["deficit_kwh_day"] * econ["horizon_days"] * econ["loss_cost_lei_per_kwh"] + fixed, 2)
    tab["score_r"] = tab["score"].round(4)
    tab["expected_value"] = np.round(tab["score_r"] * tab["value_if_true"], 2)
    tab["comm_down"] = [_trailing_gap(daily[i]) >= 2 for i in range(len(tab))]

    # alegerea: abțineri din date, apoi cele sigure după valoare, apoi cele nesigure peste un scor minim
    data_ab = tab.index[tab["data_abstain"].notna()]
    sure = tab[(tab["conformal"] == "problem") & tab["data_abstain"].isna()].sort_values("expected_value", ascending=False)
    unsure = tab[(tab["conformal"] == "unsure") & tab["data_abstain"].isna() & (tab["score"] >= MIN_REVIEW_SCORE)]
    unsure = unsure.sort_values("expected_value", ascending=False).head(MAX_REVIEW)
    action_idx = list(sure.index[:MAX_ACTION])
    watch_idx = list(sure.index[MAX_ACTION : MAX_ACTION + MAX_WATCHLIST])
    chosen = [(i, "action") for i in action_idx] + [(i, "watch") for i in watch_idx]
    chosen += [(i, "unsure") for i in unsure.index] + [(i, "data") for i in data_ab]

    rows = tab.loc[[i for i, _ in chosen]]
    labels = [lab if lab in ("faulty", "tamper") else "faulty" for lab in rows["label"]]
    factors = top_factors(model, feats.loc[rows.index], labels, k=5)
    ref = pd.read_parquet(SIMILAR_REF) if SIMILAR_REF.exists() else build_samples().query("split == 'cal'")
    sim = SimilarCases.fit(ref, model.features).query(feats.loc[rows.index], k=3)

    items, series = [], {}
    ymd = target.strftime("%Y%m%d")
    for n_row, ((i, why), fac, sims) in enumerate(zip(chosen, factors, sim, strict=True)):
        r = tab.loc[i]
        meter = r["meter_id"]
        wid = f"A-{ymd}-{meter}"
        label = labels[n_row]
        score = float(r["score_r"])
        lo = float(min(round(r["interval_low"], 4), score))
        hi = float(max(round(r["interval_high"], 4), score))
        issues = list(r["issues"])
        abstain, reason = False, None
        if why == "data":
            abstain, reason = True, str(r["data_abstain"])
        elif why == "unsure":
            abstain = True
            reason = (f"nu sunt sigur: scorul {score:.2f} e în zona în care, pe datele de calibrare, modelul nu poate "
                      "separa contoarele normale de cele cu probleme (conformal)")
        guard = False
        if label == "tamper" and not abstain and feats.loc[i, "level_kwh"] <= low_level_cut:
            guard, abstain = True, True
            reason = ("consum mic: poate fi o locuință goală sau sărăcie energetică, nu furt; "
                      "un om verifică înainte să trimitem echipa")
        if r["comm_down"]:
            issues.append("contorul nu mai comunică de cel puțin 2 zile: citirea la distanță nu e posibilă acum")
        if abstain:
            action = "human_review"
        elif why == "watch":
            action = "watchlist"
        elif label == "tamper":
            action = "inspect_on_site" if r["expected_value"] >= 0.25 * econ["visit_cost_lei"] or score >= 0.5 else "watchlist"
        elif r["comm_down"]:
            action = "inspect_on_site"
        elif feats.loc[i, "missing_recent"] >= 0.15 or score < 0.5:
            action = "remote_reading"
        else:
            action = "inspect_on_site"
        if action == "inspect_on_site":
            duration, size = int(econ["service_time_min"]), 2
            urgency = 72.0 if label == "tamper" else 120.0
        elif action == "remote_reading":
            duration, size, urgency = 5, 1, 48.0
        elif action == "watchlist":
            duration, size, urgency = 5, 1, 720.0
        else:
            duration, size, urgency = 10, 1, 48.0
        deficit = float(r["deficit_kwh_day"])
        value = float(r["value_if_true"])
        top_txt = "; ".join(f["label_ro"] for f in fac[:2])
        if abstain:
            summary = f"Nu sunt sigur ({reason}). Scor {score:.0%}. {top_txt}."
        else:
            summary = f"{LABEL_RO[label].capitalize()} ({score:.0%}): {top_txt}. Recomand: {ACTION_RO[action]}."
        if deficit > 0:
            summary += f" Lipsesc ~{deficit:.1f} kWh pe zi față de normal."
        conf = "low" if abstain else _confidence(score, str(r["conformal"]))
        item = {
            "contract_version": "1.0",
            "work_item_id": wid,
            "source": "A",
            "kind": "meter_inspection",
            "asset_id": meter,
            "asset_type": "meter",
            "location": {
                "lat": float(r["lat"]),
                "lon": float(r["lon"]),
                "zone_id": str(r["zone_id"]),
                "county": str(r["county"]),
                "label": f"Contor {meter}, {post_label.get(r['post_id'], r['post_id'])}",
            },
            "target_date": target.isoformat(),
            "prediction": {
                "model_id": "a-lgbm",
                "model_version": tab.attrs["model_version"],
                "prediction_id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"A|{scenario}|{target}|{meter}|{tab.attrs['model_version']}")),
                "label": label,
                "score": score,
                "interval_low": lo,
                "interval_high": hi,
                "point_estimate": round(deficit, 3),
                "point_unit": "kWh/zi lipsă față de normal",
                "confidence": conf,
                "abstain": abstain,
                "abstain_reason": reason,
            },
            "impact": {
                "expected_value_lei": round(score * value, 2),
                "value_if_true_lei": value,
                "customers_affected": 1,
                "urgency_hours": urgency,
                "safety_flag": bool(label == "tamper" and score >= 0.5),
                "assumptions_ref": "meters",
            },
            "effort": {"duration_min": duration, "crew_skill": "metering", "crew_size": size, "requires_planned_outage": False},
            "explanation": {"top_factors": fac[:8], "similar_cases": sims, "summary_ro": summary},
            "data_quality": {
                "missing_ratio": float(np.clip(feats.loc[i, "missing_ratio"], 0, 1)),
                "input_issues": issues,
                "synthetic": True,
                "data_sources": DATA_SOURCES,
            },
            "recommended_action": action,
            "created_at": now.isoformat(),
            "extra": {
                "series_ref": f"outputs/series/{scenario}/{wid}.json",
                "p_faulty": round(float(r.get("p_faulty", 0.0)), 4),
                "p_tamper": round(float(r.get("p_tamper", 0.0)), 4),
                "conformal": str(r["conformal"]),
                "selection": why,
                "post_id": str(r["post_id"]),
                "estimated_kwh_lost_per_day": round(deficit, 3),
                "rule_vee_fired": bool(r["rule_score"] >= 1.0),
                "smart_meter": not bool(r["comm_down"]),
                "comm_down": bool(r["comm_down"]),
                "level_kwh_day": round(float(feats.loc[i, "level_kwh"]), 3) if np.isfinite(feats.loc[i, "level_kwh"]) else None,
                "low_consumption_guard": guard,
            },
        }
        items.append(WorkItem.model_validate(item))
        series[wid] = Series.model_validate(_series(wid, meter, pop.days, daily[i], peer[i]))

    out = work_items_path(scenario, "A")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(w.model_dump_json() + "\n" for w in items), encoding="utf-8")
    sdir = OUTPUTS / "series" / scenario
    sdir.mkdir(parents=True, exist_ok=True)
    for old in sdir.glob("A-*.json"):
        old.unlink()
    for wid, s in series.items():
        (sdir / f"{wid}.json").write_text(s.model_dump_json(indent=1) + "\n", encoding="utf-8")

    truth_cols = ["meter_id", "post_id", "true_kind", "true_family", "true_problem", "true_onset_days_ago",
                  "true_kwh_lost", "true_value_lei", "input_issue", "score", "conformal", "label"]
    tab[truth_cols].to_csv(out.parent / "A_ground_truth.csv", index=False)
    emitted = {w.asset_id for w in items}
    summary = {
        "scenario": scenario,
        "target_date": target.isoformat(),
        "source_profiles_date": tab.attrs["source_date"],
        "model_version": tab.attrs["model_version"],
        "meters_scored": len(tab),
        "flagged_problem": int((tab["conformal"] == "problem").sum()),
        "flagged_unsure": int((tab["conformal"] == "unsure").sum()),
        "data_abstain": len(data_ab),
        "work_items": len(items),
        "by_action": pd.Series([w.recommended_action.value for w in items]).value_counts().to_dict(),
        "by_label": pd.Series([w.prediction.label for w in items]).value_counts().to_dict(),
        "expected_value_lei_total": round(float(sum(w.impact.expected_value_lei for w in items)), 2),
        "truth_note": "Adevărul injectat e doar pentru evaluare; agentul nu îl folosește la decizii.",
        "truth_problems_total": int(tab["true_problem"].sum()),
        "truth_problems_in_work_items": int(tab.loc[tab["meter_id"].isin(emitted), "true_problem"].sum()),
        "truth_precision_action_items": round(
            float(tab.loc[tab["meter_id"].isin([w.asset_id for w in items if not w.prediction.abstain
                                                 and w.recommended_action.value in ("inspect_on_site", "remote_reading")]),
                          "true_problem"].mean()), 4),
        "low_consumption_guard": int(sum(bool(w.extra.get("low_consumption_guard")) for w in items)),
        "created_at": now.isoformat(),
    }
    (out.parent / "A_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Lucrările A (contoare) pentru planificator")
    ap.add_argument("--scenario", default="demo-vara")
    ap.add_argument("--date", default=None, help="YYYY-MM-DD; implicit data din config/scenarios.yaml")
    args = ap.parse_args(argv)
    path = run(args.scenario, args.date)
    summary = json.loads((path.parent / "A_summary.json").read_text(encoding="utf-8"))
    print(f"scris: {path} ({summary['work_items']} lucrări)")
    print(json.dumps({k: summary[k] for k in ("target_date", "meters_scored", "flagged_problem", "flagged_unsure",
                                               "data_abstain", "by_action", "by_label", "truth_precision_action_items",
                                               "truth_problems_in_work_items", "truth_problems_total")},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
