"""Alegerea setului de features pe SETUL DE CALIBRARE (nu pe test): setul vechi față de cel nou.

    uv run python -m cyberpunks.a_contoare.select_features      # scrie reports/A/feature_selection.json

Setul "vechi" e cel de la M1 (19 zilnice + 11 la 30 de minute). Cel "nou" adaugă 10 features: scăderea și panta
față de vecini, forma distribuției, golurile separate, ritmul săptămânal, decalajul profilului zilei. A treia
variantă scoate features sezoniere brute (scăderea și panta față de propriul istoric), ca să vedem dacă ajută.
Testul nu e folosit aici; îl privim o singură dată, după alegere, în evaluate.py.
"""

from __future__ import annotations

import json
import sys

import numpy as np

from cyberpunks.a_contoare import lcl, sgcc
from cyberpunks.a_contoare import metrics as M
from cyberpunks.a_contoare.features import DAILY_FEATURES, INTRADAY_FEATURES
from cyberpunks.a_contoare.model import MeterModel
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
    out: dict = {"note": "toate cifrele sunt pe setul de calibrare; K = 1%; 'în primele 5%' = ce parte ajunge în top 5%"}
    f = sgcc.build_features()
    tr, ca = f[f.split == "train"].reset_index(drop=True), f[f.split == "cal"].reset_index(drop=True)
    k = M.k_for(len(ca))
    out["sgcc"] = {}
    for name, feats in (("vechi", OLD_DAILY), ("nou", DAILY_FEATURES)):
        m = MeterModel("sel", feats, ["normal", "tamper"]).fit(tr, tr["label"].to_numpy(), params=DETERMINISTIC)
        r = M.ranking_metrics(ca["label"].to_numpy(), m.raw_problem_score(ca), k)
        out["sgcc"][name] = {kk: round(v, 4) for kk, v in r.items()} | {"n_features": len(feats)}
        print("SGCC", name, out["sgcc"][name])

    smp = lcl.build_samples()
    tr, ca = smp[smp.split == "train"].reset_index(drop=True), smp[smp.split == "cal"].reset_index(drop=True)
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
        m = MeterModel("sel", feats, ["normal", "faulty", "tamper"]).fit(tr, y, params=DETERMINISTIC)
        s = m.raw_problem_score(ca)
        top = np.zeros(len(ca), dtype=bool)
        top[M.rank(s)[: M.k_for(len(ca), 0.05)]] = True
        kinds = {kd: round(float(top[(ca["kind"] == kd).to_numpy() & (yc == 1)].mean()), 3) for kd in WATCH_KINDS}
        benign = {kd: round(float(top[(ca["kind"] == kd).to_numpy() & (yc == 0)].mean()), 3)
                  for kd in ("vacation", "occupancy_change")}
        r = M.ranking_metrics(yc, s, k)
        out["lcl"][name] = {kk: round(v, 4) for kk, v in r.items()} | {
            "n_features": len(feats), "top5_by_kind": kinds, "top5_benign": benign}
        print("Londra", name, out["lcl"][name])
    path = REPORTS / "A" / "feature_selection.json"
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"scris: {path}")
    return out


if __name__ == "__main__":
    run()
    sys.exit(0)
