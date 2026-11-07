"""Varianta v2 a diagnosticului: ~3.000 de posturi de antrenare, trăsături noi, setări căutate automat (Optuna).

Regula: v2 se păstrează doar dacă bate v1 (varianta curentă, rezervă, neștearsă) pe același test: cele 300 de posturi
din registrul C, rețele nevăzute. Setările se aleg pe un set de validare separat de test (20% din cartierele lotului
`trainL`), niciodată pe test.

    uv run python -m cyberpunks.a_bilant.dataset --pool trainL --workers 8   # ~2 minute, ~3.000 de posturi
    uv run python -m cyberpunks.a_bilant.v2 --trials 40                     # ferestre, căutare, comparație

Scrie `reports/bilant/v2_comparison.json` (cifrele înainte și după) și, dacă v2 câștigă, `models/bilant/diagnose_v2.*`
și `reports/bilant/v2_params.json` (setările, mic, în git).
"""

from __future__ import annotations

import argparse
import json
import time

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

from cyberpunks.a_bilant import diagnose as G
from cyberpunks.a_bilant import features as F
from cyberpunks.a_bilant import normal as N
from cyberpunks.a_bilant import windows as W
from cyberpunks.a_bilant.problems import CLASSES
from cyberpunks.common.paths import DATA_PROCESSED, REPORTS

BASE = DATA_PROCESSED / "bilant"
OUT = REPORTS / "bilant"
VAL_SHARE = 0.2


def windows_big(models: dict, workers: int = 8) -> pd.DataFrame:
    p = BASE / "windows_trainL.parquet"
    if p.exists():
        return pd.read_parquet(p)
    t0 = time.perf_counter()
    d = F.load_pool("trainL")
    w = W.build_windows_parallel(d, W.predict_normal(models, d), "trainL", workers=workers)
    w.to_parquet(p)
    print(f"ferestre trainL: {len(w)} în {time.perf_counter() - t0:.0f} s")
    return w


def windows_test(models: dict) -> pd.DataFrame:
    p = BASE / "windows_pop_v2.parquet"
    if p.exists():
        return pd.read_parquet(p)
    d = F.load_pool("pop")
    w = W.build_windows(d, W.predict_normal(models, d), "pop")  # un singur proces: vecinii geografici trec de zone
    w.to_parquet(p)
    return w


def full_decision(diag: G.Diagnoser, win: pd.DataFrame) -> pd.DataFrame:
    return G.apply_martor_rule(win, G.pair_consistency(win, G.decide(diag.proba(win), win)))


def f1s(y: np.ndarray, lab: np.ndarray) -> dict:
    f = f1_score(y, lab, average=None, labels=list(CLASSES))
    return {"macro_f1": float(f.mean()), **{f"f1_{c}": float(x) for c, x in zip(CLASSES, f, strict=True)}}


def split_by_cluster(win: pd.DataFrame, seed: int = 0) -> np.ndarray:
    posts = pd.read_parquet(BASE / "trainL" / "posts.parquet")[["post_id", "cluster"]]
    cl = sorted(posts["cluster"].unique())
    rng = np.random.default_rng(seed)
    val_cl = set(rng.choice(cl, size=int(len(cl) * VAL_SHARE), replace=False))
    val_posts = set(posts.loc[posts["cluster"].isin(val_cl), "post_id"])
    return win["post_id"].isin(val_posts).to_numpy()


def tune(tr: pd.DataFrame, va: pd.DataFrame, trials: int, n_jobs: int) -> tuple[dict, float]:
    import optuna

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    yv = va["true_class"].to_numpy()

    def objective(trial: optuna.Trial) -> float:
        prm = {
            "n_estimators": trial.suggest_int("n_estimators", 200, 900, step=100),
            "learning_rate": trial.suggest_float("learning_rate", 0.02, 0.15, log=True),
            "num_leaves": trial.suggest_int("num_leaves", 15, 127, log=True),
            "min_child_samples": trial.suggest_int("min_child_samples", 10, 200, log=True),
            "subsample": trial.suggest_float("subsample", 0.5, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.4, 1.0),
            "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 10.0, log=True),
            "class_weight_power": trial.suggest_float("class_weight_power", 0.0, 1.0),
        }
        g = G.fit(tr, features=W.WIN_FEATURES_V2, params=prm, n_jobs=n_jobs)
        lab = g.proba(va).idxmax(axis=1).to_numpy()
        return float(f1_score(yv, lab, average="macro"))

    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=0))
    study.enqueue_trial({**G.DEFAULT_PARAMS, "reg_lambda": 1e-3})  # pornim de la setările v1 (reg_lambda minim al căutării)
    study.optimize(objective, n_trials=trials, show_progress_bar=False)
    return dict(study.best_params), float(study.best_value)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=40)
    ap.add_argument("--n-jobs", type=int, default=8)
    a = ap.parse_args()
    t0 = time.perf_counter()
    models = {"warm": N.load("normal"), "cold": N.load("normal_cold")}  # pierderea normală v1, antrenată pe `train`
    wl = windows_big(models, workers=a.n_jobs)
    wte = windows_test(models)
    y = wte["true_class"].to_numpy()

    # v1: modelul curent (lotul train, 300 de posturi, trăsăturile v1, setările implicite), pe același test
    v1 = G.load("diagnose")
    res_v1 = f1s(y, full_decision(v1, wte)["label"].to_numpy())

    # v2: căutarea pe validare (20% din cartierele trainL), apoi antrenare pe tot trainL
    is_val = split_by_cluster(wl)
    best, best_val = tune(wl[~is_val], wl[is_val], a.trials, a.n_jobs)
    v1_on_val = f1_score(wl.loc[is_val, "true_class"], G.fit(wl[~is_val], features=W.WIN_FEATURES_V1, n_jobs=a.n_jobs).proba(wl[is_val]).idxmax(axis=1), average="macro")
    v2 = G.fit(wl, features=W.WIN_FEATURES_V2, params=best, n_jobs=a.n_jobs)
    res_v2 = f1s(y, full_decision(v2, wte)["label"].to_numpy())
    # contribuțiile separate: doar mai multe posturi (setări v1, trăsături v1) și mai multe posturi + trăsături noi
    only_data = f1s(y, full_decision(G.fit(wl, features=W.WIN_FEATURES_V1, n_jobs=a.n_jobs), wte)["label"].to_numpy())
    data_feats = f1s(y, full_decision(G.fit(wl, features=W.WIN_FEATURES_V2, n_jobs=a.n_jobs), wte)["label"].to_numpy())
    keep = res_v2["macro_f1"] > res_v1["macro_f1"]
    out = {
        "test": "cele 300 de posturi din registrul C (rețele nevăzute), ferestre de 14 zile, model + regula de pereche + regula martorului",
        "test_windows": len(wte),
        "train_posts_v1": 300,
        "train_windows_v2": len(wl),
        "train_posts_v2": int(wl["post_id"].nunique()),
        "v1": res_v1,
        "doar_mai_multe_posturi": only_data,
        "mai_multe_posturi_si_trasaturi_noi": data_feats,
        "v2_cautare_optuna": res_v2,
        "validation_macro_f1_v2": best_val,
        "validation_macro_f1_v1_settings": float(v1_on_val),
        "best_params": best,
        "trials": a.trials,
        "v2_kept": bool(keep),
        "seconds": round(time.perf_counter() - t0, 1),
    }
    (OUT / "v2_comparison.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    if keep:
        v2.save("diagnose_v2", params=best)
        (OUT / "v2_params.json").write_text(json.dumps({"features": W.WIN_FEATURES_V2, "params": best}, indent=2))
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
