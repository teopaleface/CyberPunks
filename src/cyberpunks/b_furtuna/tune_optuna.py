"""Căutarea hiperparametrilor clasificatorului B cu Optuna (experiment pe ramura Eden).

Optuna vede DOAR anii de antrenare: fiecare încercare e notată cu PR-AUC out-of-fold (5 fold-uri pe săptămâni,
ca zilele aceleiași furtuni să nu fie și în antrenare, și în validare). Anul de test (2025) se folosește o singură
dată, la final: parametrii livrați față de cei găsiți, pe aceleași zile, cu interval bootstrap pe săptămâni.

    uv run python -m cyberpunks.b_furtuna.tune_optuna --trials 60
    uv run python -m cyberpunks.b_furtuna.tune_optuna --trials 60 --groups ore_cu_rafale,presiune --train-years 2021,2022,2023,2024

Scrie `reports/B/tuning_optuna*.json`. Studiul se salvează în `data/interim/B/optuna.db` (se poate relua).
"""

from __future__ import annotations

import argparse
import json

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss
from sklearn.model_selection import GroupKFold

from cyberpunks.b_furtuna import experiments_extra as X
from cyberpunks.b_furtuna import model as bm
from cyberpunks.b_furtuna.features import FEATURE_SPEC
from cyberpunks.common.paths import DATA_INTERIM, REPORTS

DB = DATA_INTERIM / "B" / "optuna.db"


def space(trial: optuna.Trial) -> dict:
    return {
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.1, log=True),
        "num_leaves": trial.suggest_int("num_leaves", 7, 63),
        "min_data_in_leaf": trial.suggest_int("min_data_in_leaf", 20, 400, log=True),
        "feature_fraction": trial.suggest_float("feature_fraction", 0.4, 1.0),
        "bagging_fraction": trial.suggest_float("bagging_fraction", 0.5, 1.0),
        "lambda_l2": trial.suggest_float("lambda_l2", 1e-3, 30.0, log=True),
        "min_gain_to_split": trial.suggest_float("min_gain_to_split", 0.0, 1.0),
        "rounds": trial.suggest_int("rounds", 100, 1200, step=50),
    }


def oof_pr_auc(tr: pd.DataFrame, spec: list[tuple[str, int]], over: dict) -> float:
    feats = [f for f, _ in spec]
    params = {**bm.CLF_PARAMS, **over, "monotone_constraints": [m for _, m in spec]}
    rounds = int(params.pop("rounds"))
    y = tr["event"].to_numpy()
    oof = np.zeros(len(tr))
    for a, b in GroupKFold(5).split(tr, y, bm.week_groups(tr["date"])):
        m = lgb.train(params, lgb.Dataset(tr.iloc[a][feats], label=y[a]), num_boost_round=rounds)
        oof[b] = m.predict(tr.iloc[b][feats])
    return float(average_precision_score(y, oof))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=60)
    ap.add_argument("--groups", default="", help="grupuri de variabile noi din experiments_extra.GROUPS")
    ap.add_argument("--train-years", default="2023,2024")
    a = ap.parse_args(argv)
    groups = [g for g in a.groups.split(",") if g]
    ty = tuple(int(x) for x in a.train_years.split(","))
    spec = list(FEATURE_SPEC) + [c for g in groups for c in X.GROUPS[g]]
    df = X.load()
    tr = df[df["year"].isin(ty)].reset_index(drop=True)
    tag = "_".join(["b", *groups, "ani" + "-".join(map(str, ty))])

    DB.parent.mkdir(parents=True, exist_ok=True)
    study = optuna.create_study(study_name=tag, storage=f"sqlite:///{DB}", direction="maximize", load_if_exists=True,
                                sampler=optuna.samplers.TPESampler(seed=42))
    shipped = {"learning_rate": bm.CLF_PARAMS["learning_rate"], "num_leaves": bm.CLF_PARAMS["num_leaves"],
               "min_data_in_leaf": bm.CLF_PARAMS["min_data_in_leaf"], "feature_fraction": bm.CLF_PARAMS["feature_fraction"],
               "bagging_fraction": bm.CLF_PARAMS["bagging_fraction"], "lambda_l2": bm.CLF_PARAMS["lambda_l2"],
               "min_gain_to_split": 0.0, "rounds": bm.CLF_ROUNDS}
    if not study.trials:
        study.enqueue_trial(shipped)  # prima încercare = parametrii livrați, ca referință pe aceeași validare
    left = a.trials - len(study.trials)
    if left > 0:
        study.optimize(lambda t: oof_pr_auc(tr, spec, space(t)), n_trials=left, show_progress_bar=False)
    best = study.best_params
    oof_shipped = study.trials[0].value

    # o singură dată pe test: livrat față de găsit
    p0, te = X.fit_predict(df, spec, ty, shipped)
    p1, _ = X.fit_predict(df, spec, ty, best)
    y = te["event"].to_numpy()
    lo, hi = X.paired_bootstrap(te, p0, p1)
    out = {
        "study": tag, "trials": len(study.trials), "train_years": list(ty), "features": [f for f, _ in spec],
        "validation": "PR-AUC out-of-fold, 5 fold-uri pe săptămâni, doar anii de antrenare",
        "oof_pr_auc": {"livrat": round(oof_shipped, 4), "gasit": round(study.best_value, 4)},
        "params_livrat": shipped, "params_gasit": best,
        "test_2025": {"livrat": {"pr_auc": round(float(average_precision_score(y, p0)), 4), "brier": round(float(brier_score_loss(y, p0)), 4)},
                      "gasit": {"pr_auc": round(float(average_precision_score(y, p1)), 4), "brier": round(float(brier_score_loss(y, p1)), 4)},
                      "delta_pr_auc_ci90": [round(lo, 4), round(hi, 4)]},
        "importanta_parametrilor": {k: round(v, 3) for k, v in optuna.importance.get_param_importances(study).items()},
        "istoric": [{"n": t.number, "oof_pr_auc": round(t.value, 4)} for t in study.trials if t.value is not None],
        "note": "experiment pe ramura Eden; modelul livrat nu e schimbat",
    }
    path = REPORTS / "B" / f"tuning_optuna_{tag}.json"
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("oof_pr_auc", "test_2025", "params_gasit")}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    raise SystemExit(main())
