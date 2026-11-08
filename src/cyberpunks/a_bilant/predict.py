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
from cyberpunks.a_bilant import features as F
from cyberpunks.a_bilant import inputs as I
from cyberpunks.a_bilant import normal as N
from cyberpunks.a_bilant import windows as W
from cyberpunks.a_bilant.fuse import state_path
from cyberpunks.a_bilant.martor import MARTOR_DIFF_LIMIT
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


P_DISPLAY_MAX = 0.99  # nicio probabilitate afișată nu e 100%: peste 0,99 se scrie „peste 99%”
SAFETY_P_MIN = 0.90
SAFETY_THEFT_KWH_DAY = 12.0  # ~0,5 kW medii nemăsurați, zi și noapte: legătură directă permanentă (IPOTEZĂ)
SAFETY_THEFT_NIGHT_SHARE = 0.20
SAFETY_TECH_LOSS_RATIO = 3.0  # pierderi pe cabluri de cel puțin 3 ori normalul: îmbinare care se poate încălzi (IPOTEZĂ)


def pfmt(p: float) -> str:
    """Probabilitatea pentru text: plafonată, fără „100%”."""
    return "peste 99%" if p > P_DISPLAY_MAX else f"{p:.0%}"


def safety(label: str, r: pd.Series, abstain: bool, loss_ratio: float | None) -> tuple[bool, str]:
    """Risc real pentru oameni, nu orice pierdere mare: legătură directă permanentă sau îmbinare care se încălzește."""
    if abstain or float(r["p_label"]) < SAFETY_P_MIN:
        return False, ""
    if label == "furt_inainte_contor" and float(r["r_mean_kwh"]) >= SAFETY_THEFT_KWH_DAY and float(r["night_excess_share"]) >= SAFETY_THEFT_NIGHT_SHARE:
        return True, "consum nemăsurat constant, zi și noapte: probabil legătură directă la rețea (risc de incendiu și electrocutare)"
    if label == "pierdere_tehnica" and loss_ratio is not None and loss_ratio >= SAFETY_TECH_LOSS_RATIO:
        return True, f"pierderi pe cabluri de {loss_ratio:.1f} ori normalul: o îmbinare se poate încălzi"
    return False, ""


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
    c = booster.predict(X[diag.features], pred_contrib=True)
    nf = len(diag.features) + 1
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
    if f in ("n_drop50", "top3_drop_match"):
        return f"{int(r['n_drop50'])} clienți și-au înjumătățit consumul; primii 3 explică {r['top3_drop_match']:.0%} din lipsă"
    if f in ("zero7", "const7", "neg7"):
        return f"Pe ultimele 7 zile: {int(max(r['zero7'], 0))} contoare noi cu zero, {int(r['const7'])} blocate, {int(r['neg7'])} cu semn schimbat"
    if f in ("ratio_vs_gis", "r_vs_gis_kwh"):
        return f"Postul pierde de {r['ratio_vs_gis']:.1f} ori cât îi spun cablurile din GIS și încărcarea"
    if f == "miss_share_w":
        return f"Date lipsă la contoare: {r['miss_share_w'] * 100:.1f}% din ore (completate din istoric)"
    return None


def post_states(pool: str, target_day: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Trăsăturile zilnice cu pierderea normală, fereastra zilei țintă, diagnosticul."""
    d = F.load_pool(pool)
    models = N.load_for_prediction()
    pred = W.predict_normal(models, d)
    win = W.build_windows(d, pred, pool, days=[target_day])
    diag = G.load_best()
    proba = diag.proba(win)
    dec = G.apply_martor_rule(win, G.pair_consistency(win, G.decide(proba, win)))
    d = d.assign(p10=pred["p10"].to_numpy(), p50=pred["p50"].to_numpy(), p90=pred["p90"].to_numpy())
    return d, win.join(dec), proba


def suspect_meter(cd: np.ndarray, tday: int, excess: float) -> tuple[int, str, float] | None:
    """Clientul cel mai probabil vinovat, din consumul zilnic al clienților (n, D): (index, motiv, kWh/zi).

    Întâi semnele clare din ultimele 14 zile (zile cu zero după consum normal, valoare zilnică blocată, consum
    devenit negativ), apoi consumul dispărut cel mai apropiat de lipsa postului.
    """
    if tday < 34:
        return None
    last = cd[:, tday - 13 : tday + 1]
    before = cd[:, max(0, tday - 74) : tday - 13]
    bmean = before.mean(1)
    zero = ((last == 0).sum(1) >= 5) & (bmean > 0.5)
    stuck = (np.abs(np.diff(last, axis=1)) < 1e-6).sum(1) >= 6
    stuck &= np.abs(last[:, -1]) > 0
    neg = ((last < -0.05).sum(1) >= 5) & ((before < -0.05).mean(1) < 0.05) & (bmean > 0.5)
    drop = bmean - last.mean(1)
    cands = []
    for flag, why in ((zero, "zile cu consum zero după consum normal"), (stuck, "valoare zilnică blocată"), (neg, "consum devenit negativ (polaritate)")):
        for i in np.flatnonzero(flag):
            cands.append((abs(abs(drop[i]) - abs(excess)), int(i), why, float(drop[i])))
    if cands:
        _, i, why, dr = min(cands)
        return i, why, dr
    i = int(np.argmin(np.abs(drop - excess))) if excess > 0 else int(np.argmax(drop))
    if drop[i] > 0.5:
        return i, "consum scăzut brusc, cât lipsa postului", float(drop[i])
    return None


def ensure_ready(pool: str = "pop") -> None:
    """Dintr-o clonă curată: simulează loturile (~1 minut) și antrenează modelele (~4 minute) dacă lipsesc."""
    from cyberpunks.a_bilant import dataset

    released = (N.PREVIOUS_RELEASE_DIR / "release.json").exists()
    for p in ((pool,) if released else ("train", pool)):
        if not (DATA_PROCESSED / "bilant" / p / "daily.parquet").exists():
            print(f"bilanț: lipsește lotul simulat {p}, îl construiesc (cel mult 4 procese)")
            dataset.build(p)
    if not released and (not (N.MODEL_DIR / "diagnose.txt").exists() or not (N.MODEL_DIR / "normal_q50.txt").exists()):
        print("bilanț: lipsesc modelele, rulez evaluarea (antrenare + metrici)")
        from cyberpunks.a_bilant import evaluate

        evaluate.main()


def a_items_by_post(scenario: str) -> dict[str, list[dict]]:
    """Lucrările lui A pe contoare (dacă A a rulat deja pentru scenariu), grupate pe post."""
    p = work_items_path(scenario, "A")
    out: dict[str, list[dict]] = {}
    if not p.exists():
        return out
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            w = json.loads(line)
            out.setdefault(str(w.get("extra", {}).get("post_id", "")), []).append({"id": w["work_item_id"], "meter": w["asset_id"], "action": w["recommended_action"]})
    return out


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
    sigma_path = N.PREVIOUS_RELEASE_DIR / "fusion_sigma.json" if (N.PREVIOUS_RELEASE_DIR / "release.json").exists() else N.MODEL_DIR / "fusion_sigma.json"
    sig_scale = json.loads(sigma_path.read_text()) if sigma_path.exists() else {"level": 0.9, "delta": 0.5}
    now = datetime.now(TZ).replace(microsecond=0)
    version_path = N.PREVIOUS_RELEASE_DIR / "release.json" if (N.PREVIOUS_RELEASE_DIR / "release.json").exists() else N.MODEL_DIR / "version.json"
    version = json.loads(version_path.read_text())["version"] if version_path.exists() else f"{MODEL_ID}@local"
    checks = input_checks(pool, tday, set(win["post_id"]))
    a_by_post = a_items_by_post(scenario)
    dedup = {"human_review_left_to_A": 0, "meter_work_left_to_A": 0}
    shap_idx = np.array([CLASSES.index(c) for c in win["label"]])
    diag_m = G.load_best()
    shap = _shap(diag_m, win, shap_idx)

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
            "martor_diff_pct": round(float(r["martor_diff"]) * 100, 3) if np.isfinite(float(r.get("martor_diff", float("nan")))) else None,
            "input_issues": post_issues,
        }
        if not has_bal:
            continue  # planul B: fără contor de post nu se vede lipsa (reports/bilant/plan_b.md)
        # lucrare doar dacă problema e probabilă și lipsa (sau surplusul) e mai mare decât incertitudinea normalului
        material = abs(float(r["r_mean_kwh"])) > half
        if r["p_problem"] < MIN_P_PROBLEM or not material or (r["label"] == "normal" and not r["abstain"]):
            continue
        extra: dict = {"post_id": pid, "series_ref": f"outputs/series/{scenario}/A-{target:%Y%m%d}-{pid}.json", "diagnosis_proba": {c: round(min(float(proba.loc[_, c]), P_DISPLAY_MAX), 4) for c in CLASSES}}
        md = float(r.get("martor_diff", float("nan")))
        extra["martor_check"] = {
            "rule": "contor de balanță față de contorul martor (Codul de măsurare ANRE 2015)",
            "diff_pct": round(md * 100, 3) if np.isfinite(md) else None,
            "limit_pct": MARTOR_DIFF_LIMIT * 100,
            "verdict": str(r.get("martor_rule", "fara_martor")),
        }
        # clientul suspect (cel mai mare consum dispărut) și vecinul cu surplus
        cd = cust[pid].astype(float) if pid in cust.files else None
        sus = suspect_meter(cd, tday, float(r["r_mean_kwh"])) if cd is not None else None
        if sus:
            extra["suspect_meter"] = f"{pid}-C{sus[0]:03d}"
            extra["suspect_meter_reason_ro"] = sus[1]
            extra["suspect_meter_drop_kwh_day"] = round(sus[2], 2)
        nbs = [(q, rmean.get(q, 0.0)) for q in nb.get(pid, [])]
        if nbs:
            q, v = min(nbs, key=lambda x: x[1])
            if v < -1.0:
                extra["neighbor_surplus_post"] = q
                extra["neighbor_surplus_kwh_day"] = round(float(-v), 2)
        label = r["label"]
        excess = max(float(r["r_mean_kwh"]), 0.0)
        if label in ("client_post_gresit", "contor_client") and float(r["r_mean_kwh"]) < 0:
            # surplus: clientul mutat înapoi la postul lui, sau contorul care înregistrează în plus (clientul plătește
            # energie neconsumată și trebuie despăgubit); valoarea = energia înregistrată greșit
            excess = -float(r["r_mean_kwh"])
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
        score = float(np.clip(r["p_problem"], 0, P_DISPLAY_MAX))
        # fără dubluri cu A: un post nu ajunge la om de două ori, iar munca pe contoare o face lucrarea lui A
        a_here = a_by_post.get(pid, [])
        if r["abstain"] and any(x["action"] == "human_review" for x in a_here):
            states[pid]["left_to_A"] = [x["id"] for x in a_here]
            dedup["human_review_left_to_A"] += 1
            continue
        if label == "contor_client" and not r["abstain"] and a_here:
            states[pid]["left_to_A"] = [x["id"] for x in a_here]
            dedup["meter_work_left_to_A"] += 1
            continue  # fuziunea confirmă lucrarea lui A pe contor; o lucrare de post în plus ar dubla munca
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
            feat = diag_m.features[j]
            txt = _factor_text(feat, r, extra)
            if not txt or txt in seen:
                continue
            seen.add(txt)
            v = r[feat]
            factors.append({"feature": feat, "label_ro": txt, "value": round(float(v), 3), "contribution": round(float(shap[k][j]), 4)})
            if len(factors) == 5:
                break
        lratio = extra.get("phase_rebalance_input", {}).get("loss_ratio_vs_normal")
        safe, safe_why = safety(label, r, bool(r["abstain"]), lratio)
        if safe:
            extra["safety_reason_ro"] = safe_why
        lei_month = 0.0 if label == "contor_bilant_setat" else excess * 30 * eco["price"]
        who = f"{CLASS_RO[label]}, probabil clientul {extra['suspect_meter']} ({extra['suspect_meter_reason_ro']})" if label == "contor_client" and "suspect_meter" in extra else CLASS_RO[label]
        if r["abstain"]:
            summary = f"Postul {pid}: ~{lei_month:.0f} lei pe lună pierduți peste normal. Nu sunt sigur de cauză ({r['abstain_reason']}): {CLASS_RO[label]} {pfmt(r['p_label'])} sau {CLASS_RO[r['second']]} {pfmt(r['p_second'])}. Decide un om."
        elif label == "client_post_gresit":
            side = "lipsă" if float(r["r_mean_kwh"]) > 0 else "surplus"
            mirror = str(r.get("mirror_post") or "")
            if mirror:
                extra["pair_post"] = mirror
            other = f" Perechea probabilă: {mirror}." if mirror else ""
            summary = f"Postul {pid}: {side} de ~{abs(float(r['r_mean_kwh'])):.1f} kWh/zi (~{lei_month:.0f} lei pe lună contați la postul greșit). Cauza probabilă ({pfmt(r['p_label'])}): client trecut la postul greșit în bază; tensiunea contorului seamănă cu a altui post.{other} Recomand: {ACTION_RO[action]}."
        elif label == "contor_bilant_setat":
            mtxt = f" Contorul martor diferă cu {md * 100:.1f}% (peste clasa de exactitate de {MARTOR_DIFF_LIMIT * 100:.1f}%): regula confirmă." if np.isfinite(md) and md > MARTOR_DIFF_LIMIT else ""
            summary = f"Postul {pid}: contorul de balanță arată de {r['bal_db_ratio']:.2f} ori suma clienților ({pfmt(r['p_label'])} contor de balanță defect sau setat greșit).{mtxt} Lipsa de ~{r['r_mean_kwh']:.0f} kWh/zi e doar pe hârtie. Recomand: {ACTION_RO[action]} (raportul de transformare)."
        else:
            summary = f"Postul {pid}: ~{lei_month:.0f} lei pe lună pierduți peste normal. Cauza probabilă ({pfmt(r['p_label'])}): {who}. Recomand: {ACTION_RO[action]}."
        if safe:
            summary += f" Atenție la siguranță: {safe_why}."
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
                "safety_flag": safe,
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
    print(f"{len(items)} lucrări -> {out}; {len(series)} serii; starea a {len(states)} posturi -> {sp}; fără dubluri cu A: {dedup}")
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
