"""Trăsăturile bilanțului, doar din ce știe distribuitorul: contorul de balanță, contoarele clienților din bază,
datele din GIS (lungimea și tipul cablurilor, transformatorul, numărul de clienți) și vremea.

Adevărul din construcție (coloanele `true_*`) se folosește doar pentru etichete, niciodată ca trăsătură.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from cyberpunks.a_bilant import problems as P

STATIC = ["line_km", "max_path_km", "r_max_ohm", "line_r_ohm_km", "kva", "n_customers", "n_houses", "n_prosumers", "pv_kw"]
HIST_LAG = 14  # istoricul postului se oprește cu 14 zile înainte (fereastra diagnosticului rămâne nevăzută)
HIST_SPAN = 120  # zile de istoric
NORMAL_FEATURES = [
    "abs_kwh",
    "imp_kwh",
    "exp_kwh",
    "sq_kwh2",
    "night_sq_kwh2",
    "phys_kwh",
    "own_est_kwh",
    "temp_c",
    "gti_kwh_m2",
    "miss_share",
    "hist_p20_ratio",
    "hist_p50_ratio",
    "hist_days",
    *STATIC,
]


def daily_features(daily: pd.DataFrame, posts: pd.DataFrame) -> pd.DataFrame:
    """Trăsăturile zilnice pe post, plus istoricul robust al postului (cuantila 20 și mediana raportului)."""
    d = daily.merge(posts[["post_id", *STATIC]], on="post_id", how="left").sort_values(["post_id", "day"]).reset_index(drop=True)
    d["short_kwh"] = d["bal_kwh"] - d["db_kwh"]
    # formula fizică simplă: pierderea ≈ Σ P² · R / U², cu R rezistența până la cel mai îndepărtat client
    d["phys_kwh"] = d["sq_kwh2"] * d["r_max_ohm"] / 0.4**2 / 1000.0
    d["own_est_kwh"] = d["n_customers"] * 24 * 1.5 / 1000.0  # consumul propriu tipic al contoarelor (IPOTEZĂ 1,5 W)
    d["miss_share"] = d["miss_hours"] / (24 * d["n_db"].clip(lower=1))
    ratio = (d["short_kwh"] - d["own_est_kwh"]) / d["phys_kwh"].clip(lower=1e-3)
    d["_ratio"] = ratio.clip(-50, 200)
    p20, p50, nd = [], [], []
    for _, g in d.groupby("post_id", sort=False):
        r = g["_ratio"].to_numpy()
        n = len(r)
        a20 = np.full(n, np.nan)
        a50 = np.full(n, np.nan)
        cnt = np.zeros(n)
        for i in range(n):
            lo, hi = max(0, i - HIST_LAG - HIST_SPAN), i - HIST_LAG
            if hi - lo >= 21:
                w = r[lo:hi]
                a20[i], a50[i] = np.percentile(w, [20, 50])
                cnt[i] = hi - lo
        p20.append(a20)
        p50.append(a50)
        nd.append(cnt)
    d["hist_p20_ratio"] = np.concatenate(p20)
    d["hist_p50_ratio"] = np.concatenate(p50)
    d["hist_days"] = np.concatenate(nd)
    d = d.drop(columns="_ratio")
    return d


def truth(d: pd.DataFrame, plans: dict) -> pd.DataFrame:
    """Eticheta pe post și zi: clasa problemei active cu cel mai mare exces de energie, și excesul real (kWh)."""
    d = d.copy()
    cls = np.array(["normal"] * len(d), dtype=object)
    post_kind = {}
    for pid, pl in plans.items():
        for pr in pl["problems"]:
            if pr["kind"] not in ("meter_fault", "meter_tamper"):
                post_kind[pid] = (P.KIND_CLASS[pr["kind"]], pr["onset_day"], pr["kind"])
    ex_tech = d["true_line_kwh"] - d["true_line_base_kwh"]
    ex_cfg = np.zeros(len(d))
    pk = d["post_id"].map(lambda p: post_kind.get(p, (None, 10**9, None)))
    onset = np.array([x[1] for x in pk])
    pcls = np.array([x[0] for x in pk], dtype=object)
    active = d["day"].to_numpy() >= onset
    cfg = active & (pcls == "contor_bilant_setat")
    ex_cfg[cfg] = d.loc[cfg, "bal_kwh"] / 2
    excess = (
        d["true_theft_kwh"] + d["true_meter_deficit_kwh"] + ex_tech + ex_cfg + d["true_moved_out_kwh"] - d["true_moved_in_kwh"]
    ).to_numpy()
    cls[active] = pcls[active]
    meter = (~active) & (np.abs(d["true_meter_deficit_kwh"].to_numpy()) > 0.05)
    cls[meter] = "contor_client"
    d["true_class"] = cls
    d["true_excess_kwh"] = excess
    d["clean"] = (cls == "normal") & (np.abs(d["true_meter_deficit_kwh"]) < 0.05)
    return d


def load_pool(pool: str) -> pd.DataFrame:
    """Lotul simulat (`train` sau `pop`) cu trăsături și etichete. Cere `python -m cyberpunks.a_bilant.dataset`."""
    import json

    from cyberpunks.common.paths import DATA_PROCESSED

    o = DATA_PROCESSED / "bilant" / pool
    if not (o / "daily.parquet").exists():
        raise FileNotFoundError(f"Lipsește {o}. Rulează: uv run python -m cyberpunks.a_bilant.dataset --pool {pool}")
    d = pd.read_parquet(o / "daily.parquet")
    p = pd.read_parquet(o / "posts.parquet")
    plans = json.loads((o / "plans.json").read_text())
    return truth(daily_features(d, p), plans)
