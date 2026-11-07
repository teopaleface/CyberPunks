"""Cifra „cu bilanț față de fără”: precizia contoarelor trimise la verificare în primele K și deplasările degeaba.

Pe lotul `pop` (cele 300 de posturi ale hărții), la fiecare zi de evaluare: fiecare contor are un scor de tip A, iar
o echipă verifică primele K contoare. Comparăm ordinea după scorul A singur cu ordinea după scorul combinat cu
bilanțul postului (`fuse.combine_arrays`), pe aceleași contoare și aceleași zile.

ATENȚIE: scorurile A sunt SIMULATE. Contoarele modelului A (curbe din Londra) nu sunt contoarele lumii noastre, așa
că imităm un clasificator de calitatea lui A: un semnal pentru contoarele cu problemă reală (tiparul pe care îl învață A),
plus scăderea vizibilă a consumului față de propriul istoric și tiparele evidente (zero), plus zgomot; zgomotul se
alege ca ROC-AUC-ul să fie cel raportat de A pe Londra (0,907, `reports/A/metrics.json`). Concediile și schimbările de ocupare (consum scăzut real) îl păcălesc, ca pe un model real.
Când A își leagă contoarele de posturile registrului C, cifra se reface cu scorurile lui reale.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from cyberpunks.a_bilant.fuse import combine_arrays
from cyberpunks.common.paths import DATA_PROCESSED

A_TARGET_AUC = 0.907  # reports/A/metrics.json, roc_auc pe Londra
KS = (10, 20, 50, 100)
A_SGCC_AUC = 0.8025  # reports/A/metrics.json, sgcc_roc_auc: modelul A pe date reale de furt (mai greu)
FIRST_DAY = 100


def meter_table(pool: str, win: pd.DataFrame, sigma_delta_scale: float) -> pd.DataFrame:
    """O linie pe (contor, zi de evaluare): scăderea vizibilă, adevărul, lipsa peste normal a postului."""
    o = DATA_PROCESSED / "bilant" / pool
    cust = np.load(o / "cust_daily.npz")
    plans = json.loads((o / "plans.json").read_text())
    w = win.set_index(["post_id", "day"])
    rows = []
    for pid in cust.files:
        cd = cust[pid].astype(float)
        n, _D = cd.shape
        probs = [(pr["customer"] % n, pr["onset_day"]) for pr in plans[pid]["problems"] if pr["kind"] in ("meter_fault", "meter_tamper")]
        benign = {int(k): v for k, v in plans[pid].get("benign_applied", {}).items()}
        for e in sorted({d for (p, d) in w.index if p == pid and d >= FIRST_DAY}):
            before = cd[:, e - 34 : e - 13].mean(1)
            after = cd[:, e - 6 : e + 1].mean(1)
            drop = before - after
            # pozitive: problemele apărute între e-12 și e-2 (istoricul de dinainte e curat, cel puțin 3 zile de
            # problemă); contoarele cu probleme mai vechi ies din listă (ar fi fost găsite la o tură anterioară)
            truth = np.zeros(n, bool)
            old = np.zeros(n, bool)
            for c, on in probs:
                if e - 12 <= on <= e - 2:
                    truth[c] = True
                elif on < e - 12:
                    old[c] = True
            r = w.loc[(pid, e)]
            rows.append(
                pd.DataFrame(
                    {
                        "post_id": pid,
                        "day": e,
                        "customer": np.arange(n),
                        "before": before,
                        "drop": drop,
                        "zero": (after == 0) & (before > 0.5),
                        "benign": [benign.get(i, "") for i in range(n)],
                        "truth": truth,
                        "excess": float(r["delta_kwh"]),
                        "sigma": float(r["width_kwh"]) / 2.56 * sigma_delta_scale,
                    }
                )[~old]
            )
    return pd.concat(rows, ignore_index=True)


def simulate_a_scores(t: pd.DataFrame, seed: int = 7, target_auc: float = A_TARGET_AUC) -> tuple[np.ndarray, float, float]:
    """Scoruri de tip A (vezi docstring-ul modulului). Întoarce (scor, zgomot ales, AUC obținut)."""
    share = np.clip(t["drop"] / np.maximum(np.abs(t["before"]), 0.5), -0.5, 1.5).to_numpy()
    # semnalul pe care un model bun îl prinde din tiparul contorului (3,0 la problemele reale), plus scăderea vizibilă,
    # care împinge în sus și concediile; zgomotul se alege ca AUC să fie cel al lui A
    base = -6.0 + 3.0 * t["truth"].to_numpy() + 2.0 * np.clip(share, 0, 1.5) + 2.0 * t["zero"].to_numpy()
    z = np.random.default_rng(seed).normal(0.0, 1.0, len(t))
    best = None
    for sd in np.arange(0.2, 4.01, 0.1):
        auc = roc_auc_score(t["truth"], base + sd * z)
        if best is None or abs(auc - target_auc) < abs(best[1] - target_auc):
            best = (sd, auc)
    sd, auc = best
    return 1 / (1 + np.exp(-(base + sd * z))), float(sd), float(auc)


def evaluate(t: pd.DataFrame, price_lei_kwh: float, horizon_days: int, target_auc: float = A_TARGET_AUC) -> tuple[dict, dict]:
    a, sd, auc = simulate_a_scores(t, target_auc=target_auc)
    t = t.assign(a=a, fused=combine_arrays(a, t["excess"].to_numpy(), t["sigma"].to_numpy(), np.maximum(t["drop"].to_numpy(), 0.0)))
    with_b, without = {}, {}
    for K in KS:
        pa, pf, wa, wf, va, vf = [], [], [], [], [], []
        for _, g in t.groupby("day"):
            ta = g.nlargest(K, "a")
            tf = g.nlargest(K, "fused")
            pa.append(ta["truth"].mean())
            pf.append(tf["truth"].mean())
            wa.append(K - ta["truth"].sum())
            wf.append(K - tf["truth"].sum())
            va.append((ta["truth"] * ta["drop"].clip(lower=0)).sum() * price_lei_kwh * horizon_days)
            vf.append((tf["truth"] * tf["drop"].clip(lower=0)).sum() * price_lei_kwh * horizon_days)
        without[f"precision_at_{K}"] = float(np.mean(pa))
        with_b[f"precision_at_{K}"] = float(np.mean(pf))
        without[f"wasted_trips_per_day_at_{K}"] = float(np.mean(wa))
        with_b[f"wasted_trips_per_day_at_{K}"] = float(np.mean(wf))
        without[f"value_lei_per_day_at_{K}"] = float(np.mean(va))
        with_b[f"value_lei_per_day_at_{K}"] = float(np.mean(vf))
        with_b[f"wasted_trips_avoided_per_day_at_{K}"] = float(np.mean(wa) - np.mean(wf))
    benign_mask = t["benign"] != ""
    for name, col, out in (("a", "a", without), ("fused", "fused", with_b)):
        out["roc_auc"] = float(roc_auc_score(t["truth"], t[col]))
        top = pd.concat([g.nlargest(20, col) for _, g in t.groupby("day")])
        out["benign_in_top20_per_day"] = float((top["benign"] != "").sum() / t["day"].nunique())
    info = {"a_sim_noise_sd": sd, "a_sim_auc": auc, "eval_days": int(t["day"].nunique()), "meters": int(t.groupby("day").size().mean()), "positives_per_day": float(t.groupby("day")["truth"].sum().mean()), "benign_share": float(benign_mask.mean())}
    return {**with_b, **{f"info_{k}": v for k, v in info.items()}}, without


KS_REAL = (10, 20, 50, 100, 200, 300, 500)


def evaluate_real_a(win: pd.DataFrame, sigma_delta_scale: float, price_lei_kwh: float, horizon_days: int, pool: str = "pop") -> dict:
    """Ziua demo, cu scorurile REALE ale modelului A (`A_ground_truth.csv`, toate cele ~15.850 de contoare).

    Contorul k al lui A pe un post e clientul k din lumea bilanțului (`dataset.apply_a_truth`), deci defectele lui A
    lasă energie lipsă în bilanțul postului. Lipsa estimată a contorului = scăderea consumului lui față de propriul
    istoric (ce vede distribuitorul). Pozitive = contoarele cu problemă reală după adevărul lui A.
    """
    from cyberpunks.a_bilant.dataset import a_truth

    t = a_truth()
    if t is None:
        return {}
    cust = np.load(DATA_PROCESSED / "bilant" / pool / "cust_daily.npz")
    e = int(win["day"].max())
    w = win[win["day"] == e].set_index("post_id")
    rows = []
    for pid, g in t.sort_values("meter_id").groupby("post_id"):
        if pid not in w.index or pid not in cust.files:
            continue
        cd = cust[pid].astype(float)
        k = np.arange(min(len(g), cd.shape[0]))
        before = cd[k, e - 34 : e - 13].mean(1)
        after = cd[k, e - 6 : e + 1].mean(1)
        gg = g.iloc[: len(k)]
        rows.append(pd.DataFrame({"meter_id": gg["meter_id"].to_numpy(), "post_id": pid, "a": gg["score"].to_numpy(), "truth": gg["true_problem"].to_numpy() == 1,
                                  "kwh_lost": gg["true_kwh_lost"].to_numpy(), "kind": gg["true_kind"].to_numpy(), "drop": before - after,
                                  "excess": float(w.loc[pid, "delta_kwh"]), "sigma": float(w.loc[pid, "width_kwh"]) / 2.56 * sigma_delta_scale}))
    m = pd.concat(rows, ignore_index=True)
    m["fused"] = combine_arrays(m["a"].to_numpy(), m["excess"].to_numpy(), m["sigma"].to_numpy(), np.maximum(m["drop"].to_numpy(), 0.0))
    out = {"meters": float(len(m)), "positives": float(m["truth"].sum()), "roc_auc_a": float(roc_auc_score(m["truth"], m["a"])), "roc_auc_fused": float(roc_auc_score(m["truth"], m["fused"]))}
    for K in KS_REAL:
        ta, tf = m.nlargest(K, "a"), m.nlargest(K, "fused")
        out[f"precision_at_{K}_a"] = float(ta["truth"].mean())
        out[f"precision_at_{K}_fused"] = float(tf["truth"].mean())
        out[f"wasted_trips_at_{K}_a"] = float(K - ta["truth"].sum())
        out[f"wasted_trips_at_{K}_fused"] = float(K - tf["truth"].sum())
        out[f"value_lei_at_{K}_a"] = float(ta.loc[ta["truth"], "kwh_lost"].clip(lower=0).sum() * price_lei_kwh)
        out[f"value_lei_at_{K}_fused"] = float(tf.loc[tf["truth"], "kwh_lost"].clip(lower=0).sum() * price_lei_kwh)
    # zona „nu sunt sigur” a lui A: câte trimiteri la om rezolvă bilanțul și cât de des e problemă reală acolo
    from cyberpunks.a_bilant.fuse import RESOLVE_ABSTAIN_LOG_LR

    unsure = m[t.set_index("meter_id").loc[m["meter_id"], "conformal"].to_numpy() == "unsure"]
    a = np.clip(unsure["a"], 1e-4, 1 - 1e-4)
    f = np.clip(unsure["fused"], 1e-4, 1 - 1e-4)
    llr = np.log(f / (1 - f)) - np.log(a / (1 - a))
    res = unsure[llr >= RESOLVE_ABSTAIN_LOG_LR - 1e-9]
    out["unsure_meters"] = float(len(unsure))
    out["unsure_true_rate"] = float(unsure["truth"].mean())
    out["unsure_resolved"] = float(len(res))
    out["unsure_resolved_true_rate"] = float(res["truth"].mean()) if len(res) else 0.0
    m.to_parquet(DATA_PROCESSED / "bilant" / "fusion_real_a_demo.parquet")
    return out


def invisible_energy(daily: pd.DataFrame, day: int, window: int = 14) -> dict:
    """Pe ultimele `window` zile: ce parte din energia pierdută peste normal (adevărul din construcție) nu se vede la
    niciun contor de client (furt înainte de contor, pierderi tehnice peste normal, client la postul greșit)."""
    w = daily[(daily["day"] > day - window) & (daily["day"] <= day)]
    meter = w["true_meter_deficit_kwh"].clip(lower=0).sum()
    theft = w["true_theft_kwh"].sum()
    tech = (w["true_line_kwh"] - w["true_line_base_kwh"]).clip(lower=0).sum()
    moved = w["true_moved_out_kwh"].abs().sum()  # energia contată la postul greșit (prosumatorii pot avea net negativ)
    tot = meter + theft + tech + moved
    return {"share_invisible_to_meters": float((theft + tech + moved) / tot) if tot else 0.0, "lost_kwh_day_meters": float(meter / window), "lost_kwh_day_theft": float(theft / window), "lost_kwh_day_technical": float(tech / window), "lost_kwh_day_wrong_post": float(moved / window)}


POST_CAUSES = ("furt_inainte_contor", "pierdere_tehnica", "contor_bilant_setat", "client_post_gresit")


def post_causes(win: pd.DataFrame, price_lei_kwh: float) -> dict:
    """Cauzele pe care contoarele clienților nu le văd: ce găsește bilanțul (A găsește 0 prin construcție).

    `win`: ferestrele de test cu decizia (`label`, `p_problem`, `abstain`). „Găsit” = aceeași regulă ca la lucrări
    (probabilitate de problemă ≥ 0,5 și lipsa peste incertitudinea normalului); „cauza corectă” = și clasa e cea reală.
    Energia: lipsa reală (kWh/zi) din ferestrele găsite; pentru contorul postului setat greșit lipsa e doar pe hârtie,
    deci se numără posturile, nu energia.
    """
    half = win["width_kwh"] / 2.56
    found = (win["p_problem"] >= 0.5) & (win["r_mean_kwh"].abs() > half)
    out = {}
    tot_k, tot_f = 0.0, 0.0
    for c in POST_CAUSES:
        m = win["true_class"] == c
        if not m.any():
            continue
        out[f"{c}_windows"] = float(m.sum())
        out[f"{c}_found"] = float((found & m).mean() / m.mean())
        out[f"{c}_right_cause"] = float((found & m & (win["label"] == c)).sum() / m.sum())
        if c != "contor_bilant_setat":
            ex = win.loc[m, "true_excess_kwh"].abs()
            fx = win.loc[m & found, "true_excess_kwh"].abs()
            out[f"{c}_energy_found_share"] = float(fx.sum() / ex.sum()) if ex.sum() else 0.0
            tot_k += float(ex.sum())
            tot_f += float(fx.sum())
    days = win["day"].nunique()
    out["energy_found_share"] = tot_f / tot_k if tot_k else 0.0
    out["lei_per_month_found"] = tot_f / days * 30 * price_lei_kwh
    fp = found & (win["true_class"] == "normal")
    out["false_alarm_share_of_found"] = float(fp.sum() / max(found.sum(), 1))
    return out
