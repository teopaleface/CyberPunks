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
KS = (10, 20, 50)
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


def evaluate(t: pd.DataFrame, price_lei_kwh: float, horizon_days: int) -> tuple[dict, dict]:
    a, sd, auc = simulate_a_scores(t)
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
    benign_mask = t["benign"] != ""
    for name, col, out in (("a", "a", without), ("fused", "fused", with_b)):
        out["roc_auc"] = float(roc_auc_score(t["truth"], t[col]))
        top = pd.concat([g.nlargest(20, col) for _, g in t.groupby("day")])
        out["benign_in_top20_per_day"] = float((top["benign"] != "").sum() / t["day"].nunique())
    info = {"a_sim_noise_sd": sd, "a_sim_auc": auc, "eval_days": int(t["day"].nunique()), "meters": int(t.groupby("day").size().mean()), "positives_per_day": float(t.groupby("day")["truth"].sum().mean()), "benign_share": float(benign_mask.mean())}
    return {**with_b, **{f"info_{k}": v for k, v in info.items()}}, without
