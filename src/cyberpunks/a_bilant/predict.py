"""Bilanțul pe post pentru o zi: lucrări (sursa A), serii pentru interfață și starea pentru fuziunea cu A.

    uv run python -m cyberpunks.a_bilant.predict --scenario demo-vara --date 2025-07-08

Scrie:
- `outputs/work_items/<scenariu>/A_bilant.jsonl`: o lucrare pe post cu lipsă peste normal (WorkItem, sursa A,
  `asset_type: transformer_post`, ID `A-<YYYYMMDD>-<post_id>`, `model_id` care începe cu `bilant-`);
- `outputs/series/<scenariu>/<work_item_id>.json`: „ieșit din post” (`value`) față de „suma clienților” (`expected`),
  banda pierderii normale în `low`/`high`, `flag: "lipsa_peste_normal"`;
- `outputs/bilant/<scenariu>/posts_<data>.json`: starea tuturor posturilor, citită de `fuse.fuse`.

Lumea e SIMULATĂ pe date publice (gândită pentru datele PPC): zilele de după 2025-07-08 nu există în simulare, așa
că pentru alte date se folosește ultima zi simulată, cu nota în `data_quality.input_issues`.
"""

from __future__ import annotations

import argparse
import json
import uuid
from datetime import date as Date
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from cyberpunks.a_bilant import LABEL_RO, registry, world
from cyberpunks.a_bilant import diagnose as G
from cyberpunks.a_bilant import inputs as I
from cyberpunks.a_bilant import features as F
from cyberpunks.a_bilant import normal as N
from cyberpunks.a_bilant import windows as W
from cyberpunks.a_bilant.fuse import state_path
from cyberpunks.a_bilant.problems import CLASS_RO, CLASSES
from cyberpunks.common.config import load as load_config
from cyberpunks.common.contracts import Series, WorkItem
from cyberpunks.common.paths import DATA_PROCESSED, OUTPUTS, work_items_path

TZ = ZoneInfo("Europe/Bucharest")
MODEL_ID = "bilant-diagnoza-lgbm"
MIN_P_PROBLEM = 0.5  # sub acest prag postul nu primește lucrare (doar starea pentru fuziune)
SERIES_DAYS = 60
# Cazuri de test pentru robustețe, vizibile în demo (intrări greșite SIMULATE peste datele postului)
DEMO_INPUT_FAULTS = {"PT-1003": "wh", "PT-1007": "missing_balance", "PT-1011": "duplicates"}
DATA_SOURCES = [
    "SimBench 1-LV-* (ODbL), variante sintetice (firul C)",
    "Open-Meteo archive (CC BY 4.0)",
    "Registrul posturilor firului C (poziții OpenStreetMap, ODbL)",
    "Bilanț simulat de noi: contor de post, contoarele clienților, probleme ascunse (SINTETIC)",
]
ACTION = {
    "contor_client": ("remote_reading", "metering", 10, 1, 48.0),
    "contor_bilant_setat": ("remote_reading", "metering", 10, 1, 48.0),
    "furt_inainte_contor": ("inspect_on_site", "metering", 90, 2, 72.0),
    "pierdere_tehnica": ("grid_inspection", "lv_grid", 120, 2, 168.0),
    "client_post_gresit": ("office_correction", "metering", 15, 1, 168.0),
}
ACTION_RO = {
    "remote_reading": "întâi citire la distanță și jurnalul de evenimente al contorului",
    "inspect_on_site": "verificare la fața locului",
    "grid_inspection": "echipa de rețea (cabluri, îmbinări, faze)",
    "office_correction": "corecție în bază, fără deplasare",
    "watchlist": "urmărire, fără vizită",
    "human_review": "decide un om",
}


def economics() -> dict:
    eco = load_config("economics")
    return {
        "price": float(eco["energy"]["loss_cost_lei_per_kwh"]),
        "horizon": int(eco["meters"]["detection_horizon_days"]),
        "remote_cost": float(eco["meters"]["remote_reading_cost_lei"]),
        "visit_cost": float(eco["meters"]["inspection_visit_cost_lei"]),
    }


def _phase_share_for_ratio(ratio: float, n_houses: int) -> float | None:
    """Cota fazei celei mai încărcate care ar explica o pierdere pe cabluri de `ratio` ori normalul."""
    base = world.phase_multiplier((1 / 3, 1 / 3, 1 / 3), n_houses)
    best = None
    for y in np.arange(0.34, 0.95, 0.01):
        m = world.phase_multiplier((y, (1 - y) / 2, (1 - y) / 2), n_houses) / base
        if best is None or abs(m - ratio) < abs(best[1] - ratio):
            best = (float(y), m)
    return round(best[0], 2) if best and ratio > 1.05 else None


def _shap(diag: G.Diagnoser, X: pd.DataFrame, cls_idx: np.ndarray) -> np.ndarray:
    """Contribuțiile SHAP (LightGBM pred_contrib) ale trăsăturilor la clasa aleasă, (n, F)."""
    import lightgbm as lgb

    booster = diag.model if isinstance(diag.model, lgb.Booster) else diag.model.booster_
    c = booster.predict(X[W.WIN_FEATURES], pred_contrib=True)
    nf = len(W.WIN_FEATURES) + 1
    c = np.asarray(c).reshape(len(X), len(CLASSES), nf)
    return c[np.arange(len(X)), cls_idx, :-1]


def _factor_text(feat: str, r: pd.Series, extra: dict) -> str | None:
    f = feat
    if f in ("r_mean_kwh", "r_pct", "z_mean", "days_over_p90"):
        return f"La post lipsesc ~{r['r_mean_kwh']:.1f} kWh/zi peste pierderea normală ({r['r_pct']:.1f}% din energie), {int(r['days_over_p90'])} din 14 zile peste P90"
    if f in ("delta_kwh", "jump_vs_prev", "jump_in_window"):
        return f"Lipsa a crescut cu ~{r['delta_kwh']:.1f} kWh/zi în ultima săptămână față de luna trecută"
    if f == "corr_r_load2":
        return f"Lipsa crește cu pătratul încărcării (corelație {r['corr_r_load2']:.2f}), semn de pierdere în cabluri"
    if f == "night_excess_share":
        return f"{max(min(r['night_excess_share'], 1), 0) * 100:.0f}% din lipsă apare noaptea (00-06)"
    if f == "bal_db_ratio":
        return f"Contorul postului arată de {r['bal_db_ratio']:.2f} ori suma clienților"
    if f in ("neigh_min_r_kwh", "neigh_match"):
        nb = extra.get("neighbor_surplus_post")
        return f"Postul vecin {nb or ''} are surplus de ~{-r['neigh_min_r_kwh']:.1f} kWh/zi (potrivire {r['neigh_match']:.0%})".replace("  ", " ")
    if f in ("max_drop_kwh", "drop_match", "drop_share"):
        m = extra.get("suspect_meter")
        return f"Contorul {m or 'unui client'} a scăzut cu ~{r['max_drop_kwh']:.1f} kWh/zi (explică {r['drop_match']:.0%} din lipsă)"
    if f in ("new_zero", "new_stuck", "new_neg"):
        return f"Semnale noi la contoare: {int(r['new_zero'])} zile cu zero, {int(r['new_stuck'])} blocate, {int(r['new_neg'])} negative noaptea"
    if f in ("vcorr_min", "vcorr_gap"):
        return f"Tensiunea unui contor seamănă puțin cu a postului (corelație {r['vcorr_min']:.2f} față de mediana {r['vcorr_min'] + r['vcorr_gap']:.2f})"
    if f in ("width_kwh", "p50_mean_kwh", "hist_days"):
        return f"Pierderea normală estimată: {r['p50_mean_kwh']:.1f} kWh/zi (interval P10-P90 de {r['width_kwh']:.1f} kWh)"
    if f == "miss_share_w":
        return f"Date lipsă la contoare: {r['miss_share_w'] * 100:.1f}% din ore (completate din istoric)"
    return None


def post_states(pool: str, target_day: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Trăsăturile zilnice cu pierderea normală, fereastra zilei țintă, diagnosticul."""
    d = F.load_pool(pool)
    models = {"warm": N.load("normal"), "cold": N.load("normal_cold")}
    pred = N.predict_any(models, d)
    win = W.build_windows(d, pred, pool, days=[target_day])
    diag = G.load()
    proba = diag.proba(win)
    dec = G.decide(proba, win)
    d = d.assign(p10=pred["p10"].to_numpy(), p50=pred["p50"].to_numpy(), p90=pred["p90"].to_numpy())
    return d, win.join(dec), proba


def ensure_ready(pool: str = "pop") -> None:
    """Dintr-o clonă curată: simulează loturile (~1 minut) și antrenează modelele (~4 minute) dacă lipsesc."""
    from cyberpunks.a_bilant import dataset

    for p in ("train", pool):
        if not (DATA_PROCESSED / "bilant" / p / "daily.parquet").exists():
            print(f"bilanț: lipsește lotul simulat {p}, îl construiesc (cel mult 4 procese)")
            dataset.build(p)
    if not (N.MODEL_DIR / "diagnose.txt").exists() or not (N.MODEL_DIR / "normal_q50.txt").exists():
        print("bilanț: lipsesc modelele, rulez evaluarea (antrenare + metrici)")
        from cyberpunks.a_bilant import evaluate

        evaluate.main()


def input_checks(pool: str, tday: int, post_ids: set[str]) -> dict[str, tuple[bool, list[str]]]:
    """Verificarea intrărilor pe ultimele 14 zile ale fiecărui post (`inputs.clean`), cu cazurile de test din demo."""
    wx = world.load_weather()
    hours = np.flatnonzero((wx.local_day > tday - W.WINDOW) & (wx.local_day <= tday))
    idx = wx.index[hours]
    h = np.load(DATA_PROCESSED / "bilant" / pool / "hourly.npz")
    out = {}
    for pid in post_ids:
        if f"bal__{pid}" not in h.files:
            continue
        bal = pd.Series(h[f"bal__{pid}"][hours].astype(float), index=idx)
        cust = pd.Series(h[f"db__{pid}"][hours].astype(float), index=idx)
        fault = DEMO_INPUT_FAULTS.get(pid)
        if fault == "wh":
            bal = bal * 1000
        elif fault == "missing_balance":
            bal = None
        elif fault == "duplicates":
            bal = pd.concat([bal, bal.iloc[:6] * 1.7])
        r = I.clean(bal, cust, has_prosumers=True)
        issues = [f"{x} (caz de test simulat)" if fault else x for x in r.issues]
        if r.has_balance and fault and not np.allclose(r.balance_kwh.reindex(idx).to_numpy(), h[f"bal__{pid}"][hours], rtol=1e-4, equal_nan=True):
            issues.append("corecția nu a refăcut exact datele: postul trece la verificare umană")
        out[pid] = (r.has_balance, issues)
    return out


def run(scenario: str, date: str | None = None, pool: str = "pop") -> Path:
    ensure_ready(pool)
    scen = load_config("scenarios")["scenarios"][scenario]
    raw = date or str(scen["date"])
    target = Date.today() + timedelta(days=1) if raw == "auto_tomorrow" else Date.fromisoformat(raw)
    meta = json.loads((DATA_PROCESSED / "bilant" / pool / "meta.json").read_text())
    start, end = Date.fromisoformat(meta["start"]), Date.fromisoformat(meta["end"])
    issues: list[str] = []
    sim_day = target
    if not (start + timedelta(days=60) <= target <= end):
        sim_day = end
        issues.append(f"ziua {target} nu e în simulare; folosim ultima zi simulată ({end})")
    tday = (sim_day - start).days
    eco = economics()
    d, win, proba = post_states(pool, tday)
    reg = registry.load_posts().set_index("post_id")
    nb = json.loads((DATA_PROCESSED / "bilant" / pool / "neighbors.json").read_text())
    cust = np.load(DATA_PROCESSED / "bilant" / pool / "cust_daily.npz")
    sig_scale = json.loads((N.MODEL_DIR / "fusion_sigma.json").read_text()) if (N.MODEL_DIR / "fusion_sigma.json").exists() else {"level": 0.9, "delta": 0.5}
    now = datetime.now(TZ).replace(microsecond=0)
    version = json.loads((N.MODEL_DIR / "version.json").read_text())["version"] if (N.MODEL_DIR / "version.json").exists() else f"{MODEL_ID}@local"
    checks = input_checks(pool, tday, set(win["post_id"]))
    shap_idx = np.array([CLASSES.index(c) for c in win["label"]])
    shap = _shap(G.load(), win, shap_idx)

    items, series, states = [], {}, {}
    rmean = dict(zip(win["post_id"], win["r_mean_kwh"], strict=True))
    for k, (_, r) in enumerate(win.iterrows()):
        pid = r["post_id"]
        rg = reg.loc[pid]
        pred_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"bilant|{scenario}|{target}|{pid}|{version}"))
        half = float(r["width_kwh"]) / 2.56
        has_bal, post_issues = checks.get(pid, (True, []))
        states[pid] = {
            "lat": float(rg["lat"]),
            "lon": float(rg["lon"]),
            "excess_kwh_day": round(float(r["delta_kwh"]), 3),
            "sigma_kwh_day": round(half * sig_scale["delta"], 3),
            "level_excess_kwh_day": round(float(r["r_mean_kwh"]), 3),
            "label": r["label"],
            "p_problem": round(float(r["p_problem"]), 4),
            "abstain": bool(r["abstain"]),
            "prediction_id": pred_id,
            "has_balance": has_bal,
            "input_issues": post_issues,
        }
        if not has_bal:
            continue  # planul B: fără contor de post nu se vede lipsa (reports/bilant/plan_b.md)
        # lucrare doar dacă problema e probabilă și lipsa (sau surplusul) e mai mare decât incertitudinea normalului
        material = abs(float(r["r_mean_kwh"])) > half
        if r["p_problem"] < MIN_P_PROBLEM or not material or (r["label"] == "normal" and not r["abstain"]):
            continue
        extra: dict = {"post_id": pid, "series_ref": f"outputs/series/{scenario}/A-{target:%Y%m%d}-{pid}.json", "diagnosis_proba": {c: round(float(proba.loc[_, c]), 4) for c in CLASSES}}
        # clientul suspect (cel mai mare consum dispărut) și vecinul cu surplus
        cd = cust[pid] if pid in cust.files else None
        if cd is not None and tday >= 34:
            drop = cd[:, tday - 34 : tday - 13].mean(1) - cd[:, tday - 6 : tday + 1].mean(1)
            j = int(np.argmax(drop))
            if drop[j] > 0.5:
                extra["suspect_meter"] = f"{pid}-C{j:03d}"
                extra["suspect_meter_drop_kwh_day"] = round(float(drop[j]), 2)
        nbs = [(q, rmean.get(q, 0.0)) for q in nb.get(pid, [])]
        if nbs:
            q, v = min(nbs, key=lambda x: x[1])
            if v < -1.0:
                extra["neighbor_surplus_post"] = q
                extra["neighbor_surplus_kwh_day"] = round(float(-v), 2)
        label = r["label"]
        excess = max(float(r["r_mean_kwh"]), 0.0)
        if label == "client_post_gresit" and float(r["r_mean_kwh"]) < 0:
            excess = -float(r["r_mean_kwh"])  # postul cu surplus: corecția mută clientul înapoi
        if label == "pierdere_tehnica":
            ratio = (float(r["p50_mean_kwh"]) + float(r["r_mean_kwh"])) / max(float(r["p50_mean_kwh"]), 0.1)
            share = _phase_share_for_ratio(ratio, int(rg.get("n_houses", rg.get("n_customers", 50))))
            extra["phase_rebalance_input"] = {
                "loss_ratio_vs_normal": round(ratio, 2),
                "max_phase_share_est": share,
                "note_ro": "Estimat din pierderi (fazele nu se măsoară direct): intrare pentru treapta phase_rebalance din scara de soluții a lui C.",
            }
        value = excess * eco["price"] * eco["horizon"]
        if label == "contor_bilant_setat":
            # lipsa e doar pe hârtie (contorul postului numără dublu): nu se recuperează energie, se repară datele.
            # IPOTEZĂ: valoarea = două verificări degeaba evitate (cât costă o deplasare, config/economics.yaml)
            value = 2 * eco["visit_cost"]
            extra["paper_loss_kwh_day"] = round(float(r["r_mean_kwh"]), 1)
        score = float(np.clip(r["p_problem"], 0, 1))
        if r["abstain"]:
            action, skill, dur, size, urg = "human_review", "metering", 15, 1, 72.0
        elif label in ACTION:
            action, skill, dur, size, urg = ACTION[label]
            if label == "contor_client" and "suspect_meter" not in extra:
                action, dur, size = "inspect_on_site", 40, 1  # nu știm care contor: echipa verifică la post
        else:
            action, skill, dur, size, urg = "watchlist", "metering", 5, 1, 720.0
        conf = "low" if r["abstain"] else ("high" if r["p_label"] >= 0.75 else "medium" if r["p_label"] >= 0.5 else "low")
        # factorii, ordonați după contribuția SHAP la clasa aleasă
        order = np.argsort(-np.abs(shap[k]))
        factors, seen = [], set()
        for j in order:
            feat = W.WIN_FEATURES[j]
            txt = _factor_text(feat, r, extra)
            if not txt or txt in seen:
                continue
            seen.add(txt)
            v = r[feat]
            factors.append({"feature": feat, "label_ro": txt, "value": round(float(v), 3), "contribution": round(float(shap[k][j]), 4)})
            if len(factors) == 5:
                break
        lei_month = 0.0 if label == "contor_bilant_setat" else excess * 30 * eco["price"]
        who = f", {CLASS_RO[label]} la clientul {extra['suspect_meter']}" if label == "contor_client" and "suspect_meter" in extra else f", {CLASS_RO[label]}"
        if r["abstain"]:
            summary = f"Postul {pid}: ~{lei_month:.0f} lei pe lună pierduți peste normal. Nu sunt sigur de cauză ({r['abstain_reason']}): {CLASS_RO[label]} {r['p_label']:.0%} sau {CLASS_RO[r['second']]} {r['p_second']:.0%}. Decide un om."
        elif label == "contor_bilant_setat":
            summary = f"Postul {pid}: contorul postului arată de {r['bal_db_ratio']:.2f} ori suma clienților ({r['p_label']:.0%} contor de post setat greșit). Lipsa de ~{r['r_mean_kwh']:.0f} kWh/zi e doar pe hârtie. Recomand: {ACTION_RO[action]} (raportul de transformare)."
        else:
            summary = f"Postul {pid}: ~{lei_month:.0f} lei pe lună, {r['p_label']:.0%}{who}. Recomand: {ACTION_RO[action]}."
        wid = f"A-{target:%Y%m%d}-{pid}"
        miss = float(np.clip(r["miss_share_w"], 0, 1))
        item = {
            "work_item_id": wid,
            "source": "A",
            "kind": "meter_inspection",
            "asset_id": pid,
            "asset_type": "transformer_post",
            "location": {"lat": float(rg["lat"]), "lon": float(rg["lon"]), "zone_id": str(rg["zone_id"]), "county": str(rg.get("county", "")) or None, "label": str(rg.get("label", pid))},
            "target_date": target.isoformat(),
            "prediction": {
                "model_id": MODEL_ID,
                "model_version": version,
                "prediction_id": pred_id,
                "label": label,
                "score": round(score, 4),
                "point_estimate": round(float(r["r_mean_kwh"]), 2),
                "point_unit": "kWh/zi lipsă peste pierderea normală (medie pe 14 zile)",
                "point_interval": (round(float(r["r_mean_kwh"]) - half, 2), round(float(r["r_mean_kwh"]) + half, 2)),
                "confidence": conf,
                "abstain": bool(r["abstain"]),
                "abstain_reason": r["abstain_reason"] or None,
            },
            "impact": {
                "expected_value_lei": round(score * value, 2),
                "value_if_true_lei": round(value, 2),
                "customers_affected": int(rg.get("n_customers", 0)),
                "urgency_hours": urg,
                "safety_flag": bool(label == "furt_inainte_contor"),
                "assumptions_ref": "energy.loss_cost_lei_per_kwh",
            },
            "effort": {"duration_min": dur, "crew_skill": skill, "crew_size": size, "requires_planned_outage": False},
            "explanation": {"top_factors": factors or [{"feature": "r_mean_kwh", "label_ro": "Lipsă peste normal la post", "value": round(float(r["r_mean_kwh"]), 2), "contribution": 0.0}], "summary_ro": summary},
            "data_quality": {"missing_ratio": miss, "input_issues": issues + post_issues + ([f"{miss * 100:.1f}% ore lipsă la contoare, completate din istoricul aceluiași contor"] if miss > 0 else []), "synthetic": True, "data_sources": DATA_SOURCES},
            "recommended_action": action,
            "created_at": now.isoformat(),
            "extra": {**extra, "label_ro": LABEL_RO, "lei_per_month": round(lei_month, 2), "simulated_day": sim_day.isoformat()},
        }
        items.append(WorkItem.model_validate(item))
        series[wid] = _series(wid, pid, d[d["post_id"] == pid], tday, label)

    out = work_items_path(scenario, "A_bilant")
    out.parent.mkdir(parents=True, exist_ok=True)
    items.sort(key=lambda w: -w.impact.expected_value_lei)
    out.write_text("".join(w.model_dump_json() + "\n" for w in items), encoding="utf-8")
    sdir = OUTPUTS / "series" / scenario
    sdir.mkdir(parents=True, exist_ok=True)
    for old in sdir.glob("A-*-PT-*.json"):
        old.unlink()
    for wid, s in series.items():
        (sdir / f"{wid}.json").write_text(s.model_dump_json(indent=1) + "\n", encoding="utf-8")
    sp = state_path(scenario, target)
    sp.parent.mkdir(parents=True, exist_ok=True)
    sp.write_text(json.dumps({"scenario": scenario, "date": target.isoformat(), "simulated_day": sim_day.isoformat(), "model_version": version, "loss_cost_lei_per_kwh": eco["price"], "synthetic": True, "posts": states}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(items)} lucrări -> {out}; {len(series)} serii; starea a {len(states)} posturi -> {sp}")
    return out


def _series(wid: str, pid: str, g: pd.DataFrame, tday: int, label: str) -> Series:
    g = g[(g["day"] > tday - SERIES_DAYS) & (g["day"] <= tday)].sort_values("day")
    pts = []
    for _, x in g.iterrows():
        over = x["short_kwh"] > x["p90"]
        under = x["short_kwh"] < x["p10"]
        pts.append(
            {
                "t": pd.Timestamp(x["date"]).date().isoformat(),
                "value": round(float(x["bal_kwh"]), 2),
                "expected": round(float(x["db_kwh"]), 2),
                "low": round(float(x["db_kwh"] + x["p10"]), 2),
                "high": round(float(x["db_kwh"] + x["p90"]), 2),
                "flag": "lipsa_peste_normal" if over else ("surplus_sub_normal" if under else None),
            }
        )
    r = (g["short_kwh"] - g["p50"]).to_numpy()
    ann = []
    if len(r) >= 14:
        # ziua în care lipsa peste normal a sărit cel mai mult (media pe 7 zile după față de 7 zile înainte)
        jumps = [r[i : i + 7].mean() - r[max(0, i - 7) : i].mean() for i in range(7, len(r) - 6)]
        if jumps and max(jumps) > 2:
            i = int(np.argmax(jumps)) + 7
            ann.append({"t": pd.Timestamp(g["date"].iloc[i]).date().isoformat(), "label_ro": f"Lipsa crește de aici (~{max(jumps):.1f} kWh/zi)"})
    return Series.model_validate(
        {
            "work_item_id": wid,
            "source": "A",
            "title_ro": f"{pid}: ieșit din post față de suma clienților (ultimele {SERIES_DAYS} de zile, SIMULARE)",
            "unit": "kWh",
            "points": pts,
            "thresholds": {},
            "annotations": ann,
            "synthetic": True,
        }
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", default="demo-vara")
    ap.add_argument("--date", default=None)
    a = ap.parse_args(argv)
    run(a.scenario, a.date)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
