"""Alegerea setului de features pe o VALIDARE DIN SETUL DE ANTRENARE (nu pe calibrare, nu pe test).

    uv run python -m cyberpunks.a_contoare.select_features      # scrie reports/A/feature_selection.json

Setul "vechi" e cel de la M1 (19 zilnice + 11 la 30 de minute). Cel "nou" adaugă 10 features: scăderea și panta
față de vecini, forma distribuției, golurile separate, ritmul săptămânal, decalajul profilului zilei. A treia
variantă scoate features sezoniere brute (scăderea și panta față de propriul istoric), ca să vedem dacă ajută.
Validarea: 20% din clienții (SGCC) sau gospodăriile (Londra) de antrenare, ținute deoparte; modelele candidate se
antrenează pe restul. Setul de calibrare rămâne neatins: pe el se potrivesc doar calibrarea și pragurile conformal,
deci funcția de scor e aleasă fără etichetele lor. Testul nu e folosit aici; îl privim o singură dată, în evaluate.py.
"""

from __future__ import annotations

import json
import sys

import numpy as np
from sklearn.model_selection import train_test_split

from cyberpunks.a_contoare import lcl, sgcc
from cyberpunks.a_contoare import metrics as M
from cyberpunks.a_contoare.features import DAILY_FEATURES, INTRADAY_FEATURES
from cyberpunks.a_contoare.model import MeterModel, grouped_split
from cyberpunks.a_contoare.train import DETERMINISTIC
from cyberpunks.common.paths import REPORTS

NEW_DAILY = ["max_drop_peer", "peer_ratio_slope", "half_ratio", "low_day_share", "gap_count", "q10_over_median",
             "q90_over_median", "weekly_autocorr"]
NEW_INTRADAY = ["profile_lag", "profile_lag_gain"]
OLD_DAILY = [f for f in DAILY_FEATURES if f not in NEW_DAILY]
OLD_INTRADAY = [f for f in INTRADAY_FEATURES if f not in NEW_INTRADAY]
SEASONAL_RAW = ("recent_vs_base", "max_drop", "trend_slope", "half_ratio")
WATCH_KINDS = ("clock_drift", "drift", "bypass", "h1", "night", "h6")


def run() -> dict:
    np.seterr(all="ignore")
    out: dict = {"note": ("toate cifrele sunt pe o validare din setul de antrenare (20% din clienți / gospodării, "
                          "ținute deoparte); K = 1%; 'în primele 5%' = ce parte ajunge în top 5%")}
    f = sgcc.build_features()
    full = f[f.split == "train"].reset_index(drop=True)
    i_tr, i_va = train_test_split(np.arange(len(full)), test_size=0.2, stratify=full["label"], random_state=7)
    tr, ca = full.iloc[i_tr].reset_index(drop=True), full.iloc[i_va].reset_index(drop=True)
    k = M.k_for(len(ca))
    out["sgcc"] = {}
    for name, feats in (("vechi", OLD_DAILY), ("nou", DAILY_FEATURES)):
        m = MeterModel("sel", feats, ["normal", "tamper"]).fit(tr, tr["label"].to_numpy(), params=DETERMINISTIC)
        r = M.ranking_metrics(ca["label"].to_numpy(), m.raw_problem_score(ca), k)
        out["sgcc"][name] = {kk: round(v, 4) for kk, v in r.items()} | {"n_features": len(feats)}
        print("SGCC", name, out["sgcc"][name])

    smp = lcl.build_samples()
    full = smp[smp.split == "train"].reset_index(drop=True)
    y_full = full["family"].map({"normal": 0, "faulty": 1, "tamper": 2}).to_numpy()
    i_tr, i_va = grouped_split(y_full, full["household"].to_numpy(), test_size=0.2, seed=7)
    tr, ca = full.iloc[i_tr].reset_index(drop=True), full.iloc[i_va].reset_index(drop=True)
    y = tr["family"].map({"normal": 0, "faulty": 1, "tamper": 2}).to_numpy()
    yc = ca["problem"].to_numpy()
    k = M.k_for(len(ca))
    variants = {
        "vechi": OLD_DAILY + OLD_INTRADAY,
        "nou": DAILY_FEATURES + INTRADAY_FEATURES,
        "nou_fara_sezoniere_brute": [c for c in DAILY_FEATURES + INTRADAY_FEATURES if c not in SEASONAL_RAW],
    }
    out["lcl"] = {}
    for name, feats in variants.items():
        m = MeterModel("sel", feats, ["normal", "faulty", "tamper"]).fit(tr, y, params=DETERMINISTIC,
                                                                        groups=tr["household"].to_numpy())
        s = m.raw_problem_score(ca)
        normal = ((ca["kind"] == "none") & (yc == 0)).to_numpy()

        def auc_vs_normal(mask: np.ndarray, s: np.ndarray = s, normal: np.ndarray = normal) -> float:
            if not mask.any():
                return float("nan")
            yy = np.r_[np.ones(mask.sum()), np.zeros(normal.sum())]
            return round(M.roc_auc(yy, np.r_[s[mask], s[normal]]), 4)

        # ROC-AUC pe tip, față de contoarele normale: nu depinde de prevalență (validarea are 45% probleme)
        kinds = {kd: auc_vs_normal((ca["kind"] == kd).to_numpy() & (yc == 1)) for kd in WATCH_KINDS}
        benign = {kd: auc_vs_normal((ca["kind"] == kd).to_numpy() & (yc == 0)) for kd in ("vacation", "occupancy_change")}
        r = M.ranking_metrics(yc, s, k)
        out["lcl"][name] = {kk: round(v, 4) for kk, v in r.items()} | {
            "n_features": len(feats), "auc_by_kind": kinds, "auc_benign_vs_normal": benign}
        print("Londra", name, out["lcl"][name])
    path = REPORTS / "A" / "feature_selection.json"
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"scris: {path}")
    return out


if __name__ == "__main__":
    run()
    sys.exit(0)
