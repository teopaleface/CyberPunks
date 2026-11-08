"""Benchmark furtuni (firul B): XGBoost față de LightGBM pentru probabilitatea de avarie (vârf ≥ 1% din clienți).

Protocolul livrat, neschimbat (`b_furtuna.model.train` și `b_furtuna.evaluate`):
- antrenare 2023-2024, test 2025 (an nevăzut), 80 de comitate din 8 state SUA; date REALE (EAGLE-I, Open-Meteo);
- aceleași 15 variabile și aceleași constrângeri monotone (`features.FEATURE_SPEC`);
- calibrare izotonică pe scorurile out-of-fold (5 fold-uri pe săptămâni), apoi modelul final pe toată antrenarea;
- pragul de alertă = F1 maxim pe OOF-ul calibrat (numai antrenare);
- capacitate: K = 10% din comitate pe zi (8 echipe), clienții afectați acoperiți (`evaluate.capacity_eval`).
Modelul de severitate (cuantilele P10/P50/P90) NU face parte din benchmark și nu se atinge.

Bugetul de căutare: LightGBM a fost ales dintr-o grilă de 24 de configurații pe PR-AUC OOF al anilor de antrenare
(`b_furtuna.tune`, `reports/B/tuning.json`). XGBoost primește o grilă de 24 de configurații cu aceeași structură
(complexitate × frunză minimă × pas × număr de arbori), aleasă la fel, fără să vadă 2025.

Diferențele XGBoost - LightGBM au interval bootstrap 90% pe săptămânile din 2025.

    uv run --group bench python -m cyberpunks.benchmark.furtuni            # test 2025, state nevăzute, convecție
"""

from __future__ import annotations

import argparse
import itertools
import time

import lightgbm as lgb
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import average_precision_score, brier_score_loss
from sklearn.model_selection import GroupKFold

from cyberpunks.b_furtuna import dataset
from cyberpunks.b_furtuna import experiments_extra as BX
from cyberpunks.b_furtuna import model as bm
from cyberpunks.b_furtuna.evaluate import TEST_YEAR, binary_metrics, capacity_eval, train_years
from cyberpunks.b_furtuna.features import FEATURE_SPEC
from cyberpunks.benchmark import common as C

N_THREADS = bm.N_THREADS  # 4, ca modelul livrat; XGBoost primește același număr de fire
XGB_BASE = {"objective": "binary:logistic", "tree_method": "hist", "subsample": 0.8, "colsample_bytree": 0.8,
            "reg_lambda": 1.0, "nthread": N_THREADS, "seed": 42, "eval_metric": "logloss"}
# Grila XGBoost, paralelă cu `b_furtuna.tune.GRID` (num_leaves 7/15/31 -> adâncime 3/4/5; frunza minimă în număr
# de rânduri -> greutatea minimă a hessianului, ~ rânduri × p(1-p) la prevalența ~10%).
XGB_GRID = {"max_depth": [3, 4, 5], "min_child_weight": [4.0, 10.0], "learning_rate": [0.02, 0.04], "rounds": [300, 600]}
MAX_BINS = 255


# ------------------------------------------------------------------------------------------------
# modelele, cu același protocol (OOF pe săptămâni -> izotonic -> modelul final)
# ------------------------------------------------------------------------------------------------


def lgb_fit(X: pd.DataFrame, y: np.ndarray, feats: list[str], mono: list[int], params: dict | None = None):
    p = {**bm.CLF_PARAMS, **(params or {}), "monotone_constraints": mono}
    rounds = int(p.pop("rounds", bm.CLF_ROUNDS))
    m = lgb.train(p, lgb.Dataset(X[feats], label=y), num_boost_round=rounds)
    return lambda Z: m.predict(Z[feats])


def xgb_fit(X: pd.DataFrame, y: np.ndarray, feats: list[str], mono: list[int], params: dict):
    p = {**XGB_BASE, **params, "monotone_constraints": "(" + ",".join(str(int(v)) for v in mono) + ")", "max_bin": MAX_BINS}
    rounds = int(p.pop("rounds"))
    m = xgb.train(p, xgb.DMatrix(X[feats], label=y), num_boost_round=rounds)
    return lambda Z: m.predict(xgb.DMatrix(Z[feats]))


def protocol(fit, tr: pd.DataFrame, te: pd.DataFrame, times: dict | None = None, key: str = "") -> dict:
    """OOF pe 5 fold-uri de săptămâni, calibrare izotonică pe OOF, modelul final pe toată antrenarea (`model.train`)."""
    t0 = time.perf_counter()
    y = tr["event"].to_numpy()
    oof = np.zeros(len(tr))
    for a, b in GroupKFold(n_splits=5).split(tr, y, bm.week_groups(tr["date"])):
        oof[b] = fit(tr.iloc[a], y[a])(tr.iloc[b])
    cal = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0).fit(oof, y)
    final = fit(tr, y)
    t1 = time.perf_counter()
    p = np.clip(cal.predict(final(te)), 0.0, 1.0)
    t2 = time.perf_counter()
    if times is not None:
        times[f"{key}_train_oof_calibration_final_s"] = round(t1 - t0, 3)
        times[f"{key}_predict_test_s"] = round(t2 - t1, 4)
    return {"p": p, "oof_cal": cal.predict(oof), "oof_pr_auc": float(average_precision_score(y, oof))}


def oof_pr_auc(fit, tr: pd.DataFrame) -> tuple[float, float]:
    y = tr["event"].to_numpy()
    oof = np.zeros(len(tr))
    for a, b in GroupKFold(5).split(tr, y, bm.week_groups(tr["date"])):
        oof[b] = fit(tr.iloc[a], y[a])(tr.iloc[b])
    return float(average_precision_score(y, oof)), float(brier_score_loss(y, oof))


def tune_xgb(tr: pd.DataFrame, feats: list[str], mono: list[int]) -> tuple[dict, list]:
    rows = []
    keys = list(XGB_GRID)
    for values in itertools.product(*(XGB_GRID[k] for k in keys)):
        cfg = dict(zip(keys, values, strict=True))
        ap, brier = oof_pr_auc(lambda X, y, cfg=cfg: xgb_fit(X, y, feats, mono, cfg), tr)
        rows.append({**cfg, "oof_pr_auc": C.r(ap, 4), "oof_brier": C.r(brier, 4)})
        print(f"XGBoost {cfg}: PR-AUC OOF {ap:.4f}", flush=True)
    rows.sort(key=lambda r: -r["oof_pr_auc"])
    return {k: rows[0][k] for k in keys}, rows


# ------------------------------------------------------------------------------------------------
# metrici și diferențe
# ------------------------------------------------------------------------------------------------


def chosen_mask(te: pd.DataFrame, score: np.ndarray, k: int) -> np.ndarray:
    chosen = np.zeros(len(te), bool)
    for idx in te.groupby("date").indices.values():
        chosen[idx[np.argsort(-score[idx], kind="stable")[:k]]] = True
    return chosen


def compare(te: pd.DataFrame, p0: np.ndarray, p1: np.ndarray, thr0: float, thr1: float, k: int) -> dict:
    """Metrici pentru ambele modele și diferențele XGBoost - LightGBM, bootstrap pe săptămâni (90%)."""
    te = te.reset_index(drop=True)
    y, sev, ext = te["event"].to_numpy(), te["severe"].to_numpy(), te["extreme"].to_numpy()
    weeks = bm.week_groups(te["date"])
    affected = np.where(y == 1, te["out_max"].to_numpy(), 0.0)
    c0, c1 = chosen_mask(te, p0, k), chosen_mask(te, p1, k)

    def cov(i, c):
        tot = affected[i].sum()
        return affected[i][c[i]].sum() / tot if tot > 0 else np.nan

    def ap(i, p):
        return average_precision_score(y[i], p[i]) if 0 < y[i].sum() < len(i) else np.nan

    cap = capacity_eval(te, {"lightgbm": p0, "xgboost": p1}, k)
    return {
        "lightgbm": binary_metrics(y, p0, thr0, sev, ext), "xgboost": binary_metrics(y, p1, thr1, sev, ext),
        "capacity": {"k_crews_per_day": k, "zones": int(te["fips"].nunique()), "results": cap},
        "delta_xgboost_minus_lightgbm": {
            "pr_auc": C.ci90(lambda i: ap(i, p1) - ap(i, p0), weeks),
            "brier": C.ci90(lambda i: brier_score_loss(y[i], p1[i]) - brier_score_loss(y[i], p0[i]), weeks),
            "customers_covered_share": C.ci90(lambda i: cov(i, c1) - cov(i, c0), weeks),
            "note": "Brier: o diferență NEGATIVĂ înseamnă că XGBoost e mai bine calibrat",
        },
    }


def predictions_frame(te: pd.DataFrame, p: dict[str, np.ndarray], k: int) -> pd.DataFrame:
    out = te[["fips", "state", "county", "date", "event", "severe", "extreme", "out_max", "customers"]].reset_index(drop=True)
    for name, v in p.items():
        out[f"{name}_p"] = v
        out[f"{name}_chosen_k{k}"] = chosen_mask(out, v, k)
    return out


# ------------------------------------------------------------------------------------------------


def run_main(df: pd.DataFrame, xgb_params: dict, times: dict) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    feats, mono = [f for f, _ in FEATURE_SPEC], [m for _, m in FEATURE_SPEC]
    ty = train_years(df)
    tr = df[df["year"].isin(ty) & ~df["wx_missing"]].reset_index(drop=True)
    te = df[(df["year"] == TEST_YEAR) & ~df["wx_missing"]].reset_index(drop=True)
    rl = protocol(lambda X, y: lgb_fit(X, y, feats, mono), tr, te, times, "lightgbm")
    rx = protocol(lambda X, y: xgb_fit(X, y, feats, mono, xgb_params), tr, te, times, "xgboost")
    y_tr = tr["event"].to_numpy()
    thr_l, thr_x = bm.best_f1_threshold(y_tr, rl["oof_cal"]), bm.best_f1_threshold(y_tr, rx["oof_cal"])
    k = max(1, round(0.1 * te["fips"].nunique()))
    res = compare(te, rl["p"], rx["p"], thr_l, thr_x, k)
    res["oof_pr_auc_train"] = {"lightgbm": C.r(rl["oof_pr_auc"], 4), "xgboost": C.r(rx["oof_pr_auc"], 4)}
    res["thresholds_from_train_oof"] = {"lightgbm": thr_l, "xgboost": thr_x}
    res["test_rows"], res["test_events"], res["train_rows"] = len(te), int(te["event"].sum()), len(tr)
    return res, predictions_frame(te, {"lightgbm": rl["p"], "xgboost": rx["p"]}, k), tr


def run_loso(df: pd.DataFrame, xgb_params: dict) -> dict:
    """State nevăzute, ca `evaluate.loso`: fiecare stat scos din antrenarea 2023-2024 și testat pe 2025."""
    feats, mono = [f for f, _ in FEATURE_SPEC], [m for _, m in FEATURE_SPEC]
    ty = train_years(df)
    train_df = df[df["year"].isin(ty) & ~df["wx_missing"]]
    test_df = df[(df["year"] == TEST_YEAR) & ~df["wx_missing"]]
    per, parts = {}, []
    for s in sorted(train_df["state"].unique()):
        tr, te = train_df[train_df["state"] != s].reset_index(drop=True), test_df[test_df["state"] == s].reset_index(drop=True)
        if te.empty or te["event"].sum() == 0:
            continue
        pl = protocol(lambda X, y: lgb_fit(X, y, feats, mono), tr, te)["p"]
        px = protocol(lambda X, y: xgb_fit(X, y, feats, mono, xgb_params), tr, te)["p"]
        y = te["event"].to_numpy()
        per[s] = {"events": int(y.sum()), "prevalence": C.r(y.mean(), 4),
                  "lightgbm_pr_auc": C.r(average_precision_score(y, pl)), "xgboost_pr_auc": C.r(average_precision_score(y, px)),
                  "lightgbm_brier": C.r(brier_score_loss(y, pl)), "xgboost_brier": C.r(brier_score_loss(y, px))}
        print(f"stat nevăzut {s}: LightGBM {per[s]['lightgbm_pr_auc']:.4f}, XGBoost {per[s]['xgboost_pr_auc']:.4f}", flush=True)
        parts.append(te[["state", "date", "event"]].assign(pl=pl, px=px))
    allp = pd.concat(parts, ignore_index=True)
    weeks, states = bm.week_groups(allp["date"]), allp["state"].to_numpy()
    y, pl, px = allp["event"].to_numpy(), allp["pl"].to_numpy(), allp["px"].to_numpy()
    st_idx = {s: np.flatnonzero(states == s) for s in per}

    def mean_diff(i):
        sel = np.zeros(len(y), int)
        np.add.at(sel, i, 1)  # rândurile alese, cu multiplicitate
        d = []
        for ii in st_idx.values():
            rows = np.repeat(ii, sel[ii])
            if 0 < y[rows].sum() < len(rows):
                d.append(average_precision_score(y[rows], px[rows]) - average_precision_score(y[rows], pl[rows]))
        return float(np.mean(d)) if d else np.nan

    lo = pd.DataFrame(per).T
    return {"per_state": per, "states": len(per),
            "lightgbm_pr_auc_mean": C.r(lo["lightgbm_pr_auc"].astype(float).mean()),
            "xgboost_pr_auc_mean": C.r(lo["xgboost_pr_auc"].astype(float).mean()),
            "states_xgboost_better": int((lo["xgboost_pr_auc"] > lo["lightgbm_pr_auc"]).sum()),
            "delta_mean_pr_auc": C.ci90(mean_diff, weeks, n=500),
            "bootstrap_unit": "săptămânile din 2025 (aceleași pentru toate statele), 500 de reeșantionări, 90%",
            "reference_report_lightgbm_pr_auc_mean": 0.2586}


def run_convection(xgb_params: dict, times: dict) -> dict:
    """Experiment separat: variabilele de convecție (CAPE, lifted index etc.) date AMBELOR modele."""
    df = BX.load()
    if "cape_max" not in df.columns:
        return {"skipped": "lipsesc variabilele extra (data/processed/B/us_extra_daily.parquet): "
                           "python -m cyberpunks.b_furtuna.extra_weather build"}
    spec = list(FEATURE_SPEC) + BX.GROUPS["convectie"]
    ty = (2023, 2024)
    tr = df[df["year"].isin(ty)].reset_index(drop=True)
    te = df[df["year"] == TEST_YEAR].reset_index(drop=True)
    out = {"features_added": [f for f, _ in BX.GROUPS["convectie"]], "train_years": list(ty),
           "data": "ERA5 orar (Open-Meteo) și GFS (CAPE, lifted index), REALE; tabel local", "test_rows": len(te)}
    p = {}
    for tag, sp in (("baza", list(FEATURE_SPEC)), ("convectie", spec)):
        f_, m_ = [f for f, _ in sp], [m for _, m in sp]
        rl = protocol(lambda X, y, f_=f_, m_=m_: lgb_fit(X, y, f_, m_), tr, te, times, f"conv_{tag}_lightgbm")
        rx = protocol(lambda X, y, f_=f_, m_=m_: xgb_fit(X, y, f_, m_, xgb_params), tr, te, times, f"conv_{tag}_xgboost")
        p[tag] = {"lightgbm": rl, "xgboost": rx}
    y_tr = tr["event"].to_numpy()
    k = max(1, round(0.1 * te["fips"].nunique()))
    thr = {f"{t}_{m}": bm.best_f1_threshold(y_tr, p[t][m]["oof_cal"]) for t in p for m in p[t]}
    out["with_convection"] = compare(te, p["convectie"]["lightgbm"]["p"], p["convectie"]["xgboost"]["p"],
                                     thr["convectie_lightgbm"], thr["convectie_xgboost"], k)
    weeks = bm.week_groups(te["date"])
    yv = te["event"].to_numpy()
    out["convection_gain_per_model"] = {
        m: {"pr_auc_base": C.r(average_precision_score(yv, p["baza"][m]["p"])),
            "pr_auc_convection": C.r(average_precision_score(yv, p["convectie"][m]["p"])),
            "delta": C.ci90(lambda i, m=m: average_precision_score(yv[i], p["convectie"][m]["p"][i])
                            - average_precision_score(yv[i], p["baza"][m]["p"][i]), weeks)}
        for m in ("lightgbm", "xgboost")}
    out["reference_report"] = {"lightgbm_base": 0.2777, "lightgbm_convection": 0.2865, "source": "reports/B/experiments_extra.json"}
    C.write_predictions("furtuni_convectie_test", predictions_frame(
        te, {"lightgbm": p["convectie"]["lightgbm"]["p"], "xgboost": p["convectie"]["xgboost"]["p"]}, k))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-loso", action="store_true")
    ap.add_argument("--no-convection", action="store_true")
    a = ap.parse_args(argv)
    t0 = time.perf_counter()
    df = pd.read_parquet(dataset.OUT)
    df["date"] = pd.to_datetime(df["date"])
    feats, mono = [f for f, _ in FEATURE_SPEC], [m for _, m in FEATURE_SPEC]
    tr_all = df[df["year"].isin(train_years(df)) & ~df["wx_missing"]].reset_index(drop=True)
    times: dict = {}
    with C.timer(times, "xgboost_grid_search_s"):
        best, grid = tune_xgb(tr_all, feats, mono)
    print(f"XGBoost ales pe OOF: {best}", flush=True)
    main_res, preds, _ = run_main(df, best, times)
    ref = {"pr_auc": 0.2777, "brier": 0.0841, "capacity_customers_covered": 0.1671, "source": "reports/B/metrics.json"}
    got = {"pr_auc": round(main_res["lightgbm"]["pr_auc"], 4), "brier": round(main_res["lightgbm"]["brier"], 4),
           "capacity_customers_covered": main_res["capacity"]["results"]["lightgbm"]["customers_covered_share"]}
    out = {
        "problem": "furtuni: probabilitatea zilei cu vârf ≥ 1% din clienți fără curent (zonă × zi)",
        "data": "EAGLE-I (ORNL, CC BY 4.0) și Open-Meteo, REALE; 80 de comitate din 8 state SUA",
        "split": f"pe timp: antrenare {train_years(df)}, test {TEST_YEAR}",
        "features": feats, "monotone_constraints": dict(zip(feats, mono, strict=True)),
        "calibration": "izotonică pe OOF (5 fold-uri pe săptămâni), identică pentru ambele",
        "severity_model": "neschimbat (cuantilele LightGBM), în afara benchmarkului",
        "tuning_budget": {"lightgbm": "24 de configurații pe PR-AUC OOF (reports/B/tuning.json)",
                          "xgboost": "24 de configurații pe PR-AUC OOF, aceeași structură a grilei"},
        "xgboost_params": {**XGB_BASE, **best, "max_bin": MAX_BINS}, "xgboost_grid": grid,
        "lightgbm_params": {k: v for k, v in bm.CLF_PARAMS.items() if k != "monotone_constraints"} | {"rounds": bm.CLF_ROUNDS},
        "reference_check": {"report": ref, "reproduced": got, "matches_report": all(abs(got[m] - ref[m]) < 1e-9 for m in got)},
        "test_2025": main_res,
        "bootstrap_unit": "săptămâna ISO din 2025, 1000 de reeșantionări, 90%",
    }
    C.write_predictions("furtuni_test2025", preds)
    if not a.no_loso:
        with C.timer(times, "loso_both_s"):
            out["unseen_states"] = run_loso(df, best)
    if not a.no_convection:
        out["convection_experiment"] = run_convection(best, times)
    out["timing_s"] = {**times, "threads": N_THREADS, "test_rows": main_res["test_rows"]}
    out["environment"] = C.environment()
    out["seconds_total"] = round(time.perf_counter() - t0, 1)
    C.write_json("furtuni", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
