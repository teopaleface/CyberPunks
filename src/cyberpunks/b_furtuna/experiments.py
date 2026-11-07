"""Experimentele modelului B („ce am încercat”), reproductibile. Fiecare variantă se antrenează pe 2023-2024 și se
testează pe 2025, cu aceleași fold-uri și aceeași calibrare. Rezultatele ajung în `reports/B/experiments.json`
și în secțiunea „Ce am încercat” din `reports/B/error_analysis.md`.

    uv run python -m cyberpunks.b_furtuna.experiments
"""

from __future__ import annotations

import json
from collections.abc import Callable

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import average_precision_score, brier_score_loss

from cyberpunks.b_furtuna import dataset
from cyberpunks.b_furtuna import model as bm
from cyberpunks.b_furtuna.evaluate import TEST_YEAR, TRAIN_YEARS
from cyberpunks.b_furtuna.features import FEATURE_SPEC
from cyberpunks.common.paths import REPORTS

OUT = REPORTS / "B" / "experiments.json"


def add_gust_climate(df: pd.DataFrame) -> pd.DataFrame:
    """Rafala față de clima locului: media și percentila 95 a rafalei zilnice pe anii de antrenare, pe comitat."""
    ref = df[df["year"].isin(TRAIN_YEARS)].groupby("fips")["gust_max"].agg(g_mean="mean", g_p95=lambda s: s.quantile(0.95))
    df = df.merge(ref, on="fips", how="left")
    df["gust_anom"] = df["gust_max"] - df["g_mean"]
    df["gust_ratio_p95"] = df["gust_max"] / df["g_p95"]
    return df


def add_precip_extra(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["fips", "date"])
    df["precip_intensity"] = df["precip"] / df["precip_hours"].clip(lower=1)
    df["precip_30d"] = df.groupby("fips")["precip"].transform(lambda s: s.rolling(30, min_periods=10).sum())
    return df


def run_variant(df: pd.DataFrame, spec: list[tuple[str, int]], event_col: str = "event", monotone: bool = True,
                params_over: dict | None = None) -> dict:
    feats = [f for f, _ in spec]
    params = {**bm.CLF_PARAMS, **(params_over or {})}
    params["monotone_constraints"] = [m for _, m in spec] if monotone else [0] * len(spec)
    tr = df[df["year"].isin(TRAIN_YEARS)].reset_index(drop=True)
    te = df[df["year"] == TEST_YEAR].reset_index(drop=True)
    y_tr, y_te = tr[event_col].to_numpy(), te[event_col].to_numpy()

    def fit(X, y):
        import lightgbm as lgb
        return lgb.train(params, lgb.Dataset(X[feats], label=y), num_boost_round=params.pop("rounds", bm.CLF_ROUNDS)
                         if "rounds" in params else bm.CLF_ROUNDS)

    groups = bm.week_groups(tr["date"])
    oof = np.zeros(len(tr))
    from sklearn.model_selection import GroupKFold
    for a, b in GroupKFold(5).split(tr, y_tr, groups):
        oof[b] = fit(tr.iloc[a], y_tr[a]).predict(tr.iloc[b][feats])
    cal = IsotonicRegression(out_of_bounds="clip").fit(oof, y_tr)
    p = cal.predict(fit(tr, y_tr).predict(te[feats]))
    return {"pr_auc": round(float(average_precision_score(y_te, p)), 4),
            "brier": round(float(brier_score_loss(y_te, p)), 4),
            "prevalence": round(float(y_te.mean()), 4)}


def experiments() -> list[tuple[str, str, Callable[[pd.DataFrame], dict]]]:
    base = list(FEATURE_SPEC)
    no_lags = [(f, m) for f, m in base if f not in ("gust_prev", "gust_max_2d", "precip_7d", "snow_3d")]
    weather_only = [(f, m) for f, m in base if f not in ("log_customers", "log_density")]
    clim = base + [("gust_anom", 1), ("gust_ratio_p95", 1)]
    extra = base + [("precip_intensity", 1), ("precip_30d", 0)]
    return [
        ("baza", "features-urile din features.py, constrângeri monotone", lambda d: run_variant(d, base)),
        ("fara_monotonie", "fără constrângeri monotone", lambda d: run_variant(d, base, monotone=False)),
        ("fara_intarzieri", "fără vremea din zilele precedente", lambda d: run_variant(d, no_lags)),
        ("doar_vreme", "fără mărimea și densitatea zonei", lambda d: run_variant(d, weather_only)),
        ("clima_locala", "+ rafala față de clima comitatului (medie, p95 pe anii de antrenare)",
         lambda d: run_variant(d, clim)),
        ("ploaie_extra", "+ intensitatea ploii și ploaia pe 30 de zile", lambda d: run_variant(d, extra)),
        ("prag_2pct", "evenimentul la ≥ 2% din clienți (în loc de 1%)",
         lambda d: run_variant(d.assign(ev2=(d["pct_out_max"] >= 0.02).astype(int)), base, event_col="ev2")),
        ("prag_5pct", "evenimentul la ≥ 5% din clienți",
         lambda d: run_variant(d.assign(ev5=(d["pct_out_max"] >= 0.05).astype(int)), base, event_col="ev5")),
        ("arbori_mai_mari", "num_leaves 31, min_data_in_leaf 20",
         lambda d: run_variant(d, base, params_over={"num_leaves": 31, "min_data_in_leaf": 20})),
    ]


def main() -> int:
    df = pd.read_parquet(dataset.OUT)
    df["date"] = pd.to_datetime(df["date"])
    df = df[~df["wx_missing"]]
    df = add_precip_extra(add_gust_climate(df))
    rows = []
    for name, desc, fn in experiments():
        r = fn(df)
        rows.append({"varianta": name, "ce": desc, **r})
        print(f"{name:16s} PR-AUC {r['pr_auc']:.4f}  Brier {r['brier']:.4f}  (prevalență {r['prevalence']:.3f})")
    meta = {"counties": int(df["fips"].nunique()), "train": f"{TRAIN_YEARS[0]}-{TRAIN_YEARS[1]}", "test": TEST_YEAR}
    OUT.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(meta))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
