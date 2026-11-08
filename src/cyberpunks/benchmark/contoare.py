"""Benchmark contoare (firul A): CatBoost față de LightGBM, aceleași date, aceleași variabile, același protocol.

Trei seturi, raportate SEPARAT:
- `sgcc`: SGCC, consum zilnic REAL cu etichete REALE de furt; împărțire pe clienți 60/20/20 (`sgcc.split_customers`).
- `lcl_baza`: Low Carbon London, consum REAL, probleme INJECTATE (etichete SINTETICE); 45 de fișiere, gospodării
  nevăzute și perioadă ulterioară (sept. 2013 - feb. 2014), ca modelul livrat `a-lgbm`.
- `lcl_extins`: aceeași calibrare și același test, plus gospodăriile din celelalte 123 de fișiere LCL la antrenare
  (`experiments_extra.mai_multe_gospodarii`).

Ambele modele: aceeași împărțire internă pentru oprirea timpurie (15% din gospodăriile de antrenare, `grouped_split`;
pe SGCC 15% stratificat), aceeași calibrare Venn-ABERS și aceleași praguri conformal pe setul de calibrare. Nicio
căutare de hiperparametri pentru niciunul (LightGBM: setările livrate, alese de mână; Optuna nu le-a bătut, vezi
`reports/A/tuning_optuna.json`; CatBoost: setările echivalente, alese înainte de a vedea testul).

Valorile K sunt cele din `a_contoare.evaluate` (K principal = 1% din contoarele din test).

    uv run --group bench python -m cyberpunks.benchmark.contoare
"""

from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.model_selection import train_test_split

from cyberpunks.a_contoare import experiments_extra as X
from cyberpunks.a_contoare import metrics as M
from cyberpunks.a_contoare import sgcc
from cyberpunks.a_contoare.evaluate import OBVIOUS_KINDS, per_kind
from cyberpunks.a_contoare.features import ALL_FEATURES, DAILY_FEATURES
from cyberpunks.a_contoare.inject import TAMPER_KINDS
from cyberpunks.a_contoare.model import MeterModel, git_sha, grouped_split
from cyberpunks.a_contoare.train import ALPHA_NORMAL, ALPHA_PROBLEM, DETERMINISTIC, FAMILY_TO_Y, LCL_CLASSES
from cyberpunks.benchmark import common as C

N_JOBS = 4  # ca în `a_contoare.model.N_JOBS`; CatBoost primește același număr de fire
# Setările CatBoost: echivalentele directe ale celor LightGBM livrate (pas 0,03, 3.000 de arbori cu oprire după 100,
# 80% din rânduri și coloane, clase echilibrate, regularizare L2), adâncime 6 (implicită; ~ 31 de frunze la LightGBM).
CAT_PARAMS = {"iterations": 3000, "learning_rate": 0.03, "depth": 6, "l2_leaf_reg": 3.0, "rsm": 0.8,
              "bootstrap_type": "Bernoulli", "subsample": 0.8, "auto_class_weights": "Balanced"}


class CatMeterModel(MeterModel):
    """`MeterModel` cu CatBoost în loc de LightGBM; calibrarea, conformal și predicția sunt moștenite neschimbate."""

    def fit(self, x: pd.DataFrame, y: np.ndarray, seed: int = 42, params: dict | None = None,
            groups: np.ndarray | None = None) -> CatMeterModel:
        y = np.asarray(y).astype(int)
        if groups is None:
            tr, va = train_test_split(np.arange(len(y)), test_size=0.15, stratify=y, random_state=seed)
        else:
            tr, va = grouped_split(y, groups, test_size=0.15, seed=seed)
        multiclass = len(self.classes) > 2
        p = {**CAT_PARAMS, **(params or {})}
        self.clf = CatBoostClassifier(loss_function="MultiClass" if multiclass else "Logloss",
                                      eval_metric="MultiClass" if multiclass else "PRAUC",
                                      od_type="Iter", od_wait=100, use_best_model=True, random_seed=seed,
                                      thread_count=N_JOBS, verbose=0, allow_writing_files=False, **p)
        xf = x[self.features].replace([np.inf, -np.inf], np.nan)
        self.clf.fit(xf.iloc[tr], y[tr], eval_set=(xf.iloc[va], y[va]))
        self.meta["best_iteration"] = int(self.clf.get_best_iteration() or p["iterations"])
        self.meta["n_train"] = len(tr)
        self.version = f"{self.model_id}@{git_sha()}"
        return self

    def raw_proba(self, x: pd.DataFrame) -> np.ndarray:
        return self.clf.predict_proba(x[self.features].replace([np.inf, -np.inf], np.nan))


def fit_both(train: pd.DataFrame, cal: pd.DataFrame, y_train: np.ndarray, y_cal: np.ndarray, feats: list[str],
             classes: list[str], groups: np.ndarray | None, times: dict) -> dict[str, MeterModel]:
    out = {}
    for name, cls, params in (("lightgbm", MeterModel, DETERMINISTIC), ("catboost", CatMeterModel, None)):
        with C.timer(times, f"{name}_train_s"):
            m = cls(f"bench-{name}", feats, classes).fit(train, y_train, params=params, groups=groups)
            m.calibrate(cal, y_cal, alpha_normal=ALPHA_NORMAL, alpha_problem=ALPHA_PROBLEM)
        times[f"{name}_trees"] = m.meta["best_iteration"]
        out[name] = m
    return out


def predict_both(models: dict[str, MeterModel], test: pd.DataFrame, times: dict) -> dict[str, pd.DataFrame]:
    out = {}
    for name, m in models.items():
        with C.timer(times, f"{name}_predict_test_s"):
            out[name] = m.predict(test)
    return out


def ranking(y: np.ndarray, s: np.ndarray, ks: list[int]) -> dict:
    return {"pr_auc": C.r(M.pr_auc(y, s)), "roc_auc": C.r(M.roc_auc(y, s)),
            "precision_at_k": {str(k): C.r(M.precision_at_k(y, s, k)) for k in sorted(set(ks))},
            "recall_at_k": {str(k): C.r(M.recall_at_k(y, s, k)) for k in sorted(set(ks))}}


def deltas(y: np.ndarray, s0: np.ndarray, s1: np.ndarray, k: int, groups: np.ndarray) -> dict:
    """CatBoost - LightGBM: PR-AUC și precizia la K (K scalat la mărimea fiecărei reeșantionări, ca în evaluate)."""
    n = len(y)

    def pk(i, s):
        return M.precision_at_k(y[i], s[i], max(1, round(len(i) * k / n)))

    def ok(i):
        return 0 < y[i].sum() < len(i)

    return {"pr_auc": C.ci90(lambda i: M.pr_auc(y[i], s1[i]) - M.pr_auc(y[i], s0[i]) if ok(i) else np.nan, groups),
            f"precision_at_{k}": C.ci90(lambda i: pk(i, s1) - pk(i, s0) if ok(i) else np.nan, groups)}


def calib(y: np.ndarray, p: np.ndarray) -> dict:
    return {"brier": C.r(M.brier(y, p)), "ece": C.r(M.ece(y, p))}


# ------------------------------------------------------------------------------------------------


def run_sgcc() -> dict:
    t0 = time.perf_counter()
    times: dict = {}
    f = sgcc.build_features()
    tr, ca, te = (f[f.split == x].reset_index(drop=True) for x in ("train", "cal", "test"))
    models = fit_both(tr, ca, tr["label"].to_numpy(), ca["label"].to_numpy(), DAILY_FEATURES, ["normal", "tamper"], None, times)
    pred = predict_both(models, te, times)
    y = te["label"].to_numpy()
    k = M.k_for(len(y))
    pos = int(y.sum())
    ks = [50, k, 100, 200, 400, pos, 2 * pos]  # ca în evaluate.ranking_at_ks
    s = {n: p["score"].to_numpy() for n, p in pred.items()}
    groups = te["customer_id"].to_numpy()  # un rând pe client: bootstrap pe clienți
    res = {
        "data": "SGCC, consum zilnic REAL, etichete REALE de furt (Zheng et al. 2018); fără licență explicită: "
                "predicțiile pe client rămân locale, în data/processed/benchmark/",
        "split": "pe clienți, stratificat: 60% antrenare, 20% calibrare, 20% test (seed 42)",
        "n_test": len(y), "positives_test": pos, "k_main": k, "ks": sorted(set(ks)),
        "bootstrap_unit": "clientul (un rând pe client)",
        "reference_report": {"pr_auc": 0.3994, "precision_at_85": 0.8, "source": "reports/A/metrics_full.json"},
        **{n: {**ranking(y, s[n], ks), "calibration": calib(y, s[n])} for n in s},
        "delta_catboost_minus_lightgbm": deltas(y, s["lightgbm"], s["catboost"], k, groups),
        "timing_s": {**times, "threads": N_JOBS, "test_rows": len(y)},
        "seconds_total": round(time.perf_counter() - t0, 1),
    }
    out = te[["customer_id", "label"]].copy()
    for n, p in pred.items():
        out[f"{n}_score"], out[f"{n}_raw"] = p["score"].to_numpy(), p["raw_score"].to_numpy()
    C.write_predictions("contoare_sgcc_test", out, local=True)
    return res


def lcl_block(name: str, train: pd.DataFrame, cal: pd.DataFrame, test: pd.DataFrame) -> dict:
    t0 = time.perf_counter()
    times: dict = {}
    feats = list(ALL_FEATURES)
    models = fit_both(train, cal, train["family"].map(FAMILY_TO_Y).to_numpy(), cal["problem"].to_numpy(), feats,
                      LCL_CLASSES, train["household"].to_numpy(), times)
    pred = predict_both(models, test, times)
    y = test["problem"].to_numpy()
    hh = test["household"].to_numpy()
    s = {n: p["score"].to_numpy() for n, p in pred.items()}
    subtle = ~(test["kind"].isin(OBVIOUS_KINDS) & (test["problem"] == 1)).to_numpy()
    k = M.k_for(len(y))
    ks_full = [50, 100, k, 200, 300, 400, int(y.sum()), 2 * int(y.sum())]  # ca în evaluate
    ys, ks_sub = y[subtle], M.k_for(int(subtle.sum()))
    ks_subtle = [50, 100, ks_sub, 200, int(ys.sum())]
    # furtul: doar manipulările subtile față de contoarele fără problemă (defectele scoase)
    theft = (test["problem"].to_numpy() == 0) | test["kind"].isin(TAMPER_KINDS).to_numpy()
    yt = y[theft]
    res = {
        "n_train": len(train), "households_train": int(train["household"].nunique()),
        "n_test": len(y), "positives_test": int(y.sum()), "households_test": len(np.unique(hh)),
        "n_subtle": int(subtle.sum()), "positives_subtle": int(ys.sum()), "k_main": k, "k_top1pct_subtle": ks_sub,
        "full_test": {n: {**ranking(y, s[n], ks_full), "calibration": calib(y, s[n])} for n in s},
        "subtle": {n: {**ranking(ys, s[n][subtle], ks_subtle),
                       "precision_top1pct": C.r(M.precision_at_k(ys, s[n][subtle], ks_sub))} for n in s},
        "tamper_only": {n: {"pr_auc": C.r(M.pr_auc(yt, s[n][theft])),
                            "precision_at_k": C.r(M.precision_at_k(yt, s[n][theft], M.k_for(int(theft.sum()))))} for n in s},
        "delta_catboost_minus_lightgbm": {
            "full_test": deltas(y, s["lightgbm"], s["catboost"], k, hh),
            "subtle": deltas(ys, s["lightgbm"][subtle], s["catboost"][subtle], ks_sub, hh[subtle]),
            "tamper_only": deltas(yt, s["lightgbm"][theft], s["catboost"][theft], M.k_for(int(theft.sum())), hh[theft]),
        },
        "per_kind": {n: per_kind(test, s[n]) for n in s},
        "timing_s": {**times, "threads": N_JOBS, "test_rows": len(y)},
        "seconds": round(time.perf_counter() - t0, 1),
    }
    out = test[["sample_id", "household", "date", "kind", "family", "problem"]].copy()
    out["subtle"] = subtle
    for n, p in pred.items():
        out[f"{n}_score"], out[f"{n}_raw"], out[f"{n}_label"] = p["score"].to_numpy(), p["raw_score"].to_numpy(), p["label"].to_numpy()
    C.write_predictions(f"contoare_{name}_test", out)
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skip-extended", action="store_true", help="fără setul LCL extins (168 de fișiere)")
    a = ap.parse_args(argv)
    np.seterr(all="ignore")
    MeterModel.save = lambda self, *a, **k: None  # benchmarkul nu scrie în models/
    t0 = time.perf_counter()
    temp = X.london_temperature()
    base = X.base_samples(temp)
    tr, ca, te = (base[base.split == x].reset_index(drop=True) for x in ("train", "cal", "test"))
    out = {
        "problem": "contoare: clasament al contoarelor suspecte (scor calibrat de problemă)",
        "features": {"sgcc": DAILY_FEATURES, "lcl": list(ALL_FEATURES)},
        "tuning_budget": "zero încercări pentru ambele: setările LightGBM livrate și setările CatBoost echivalente, "
                         "fixate înainte de test; oprirea timpurie pe 15% din antrenare (gospodării întregi la LCL)",
        "calibration": "Venn-ABERS și conformal (alpha normal 1%, problemă 30%) pe setul de calibrare, identic",
        "catboost_params": CAT_PARAMS,
        "sgcc_real_labels": run_sgcc(),
        "lcl_baza": {"labels": "SINTETICE: probleme injectate peste consum REAL (LCL, CC BY 4.0)",
                     "reference_report": {"subtle_precision_at_k": 0.625, "subtle_pr_auc": 0.4057, "pr_auc": 0.6778,
                                          "source": "reports/A/metrics_full.json, reports/A/experiments_extra.json (baza)"},
                     **lcl_block("lcl_baza", tr, ca, te)},
    }
    if not a.skip_extended:
        extra = X.extra_train_samples(temp)
        out["lcl_extins"] = {"labels": "SINTETICE: probleme injectate peste consum REAL; gospodăriile în plus doar la antrenare",
                             "reference_report": {"subtle_precision_at_k": 0.8906, "subtle_pr_auc": 0.5175, "pr_auc": 0.7344,
                                                  "source": "reports/A/experiments_extra.json (mai_multe_gospodarii)"},
                             **lcl_block("lcl_extins", pd.concat([tr, extra], ignore_index=True), ca, te)}
    for key, block in ((k, out[k]) for k in ("lcl_baza", "lcl_extins") if k in out):
        ref, lg = block["reference_report"], block
        got = {"subtle_precision_at_k": lg["subtle"]["lightgbm"]["precision_top1pct"],
               "subtle_pr_auc": lg["subtle"]["lightgbm"]["pr_auc"], "pr_auc": lg["full_test"]["lightgbm"]["pr_auc"]}
        block["reference_check"] = {"reproduced": got, "matches_report": all(abs(round(got[m], 4) - ref[m]) < 1e-9 for m in got)}
    sg = out["sgcc_real_labels"]
    got = {"pr_auc": sg["lightgbm"]["pr_auc"], "precision_at_85": sg["lightgbm"]["precision_at_k"].get("85")}
    sg["reference_check"] = {"reproduced": got, "matches_report": all(
        v is not None and abs(round(v, 4) - sg["reference_report"][m]) < 1e-9 for m, v in got.items())}
    out["environment"] = C.environment()
    out["seconds_total"] = round(time.perf_counter() - t0, 1)
    C.write_json("contoare", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
