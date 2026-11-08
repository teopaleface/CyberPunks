"""Căutarea hiperparametrilor modelului A cu Optuna (experiment pe ramura Eden).

Datele: varianta câștigătoare din `experiments_extra` (toate cele 168 de fișiere Low Carbon London la antrenare).
Optuna vede DOAR antrenarea: fiecare încercare se antrenează pe 80% din gospodăriile de antrenare și e notată cu
PR-AUC pe problemele subtile din celelalte 20% (gospodării întregi, nevăzute). Calibrarea și testul nu sunt atinse.
La final, o singură dată pe testul livrat: parametrii livrați față de cei găsiți, cu interval bootstrap.

    uv run python -m cyberpunks.a_contoare.experiments_extra   # o dată, construiește eșantioanele
    uv run python -m cyberpunks.a_contoare.tune_optuna --trials 30

Etichetele sunt SINTETICE (probleme injectate peste consum real).
"""

from __future__ import annotations

import argparse
import json

import numpy as np
import optuna
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

from cyberpunks.a_contoare import experiments_extra as X
from cyberpunks.a_contoare import features as F
from cyberpunks.a_contoare import metrics as M
from cyberpunks.a_contoare.evaluate import OBVIOUS_KINDS
from cyberpunks.a_contoare.model import LGBM_PARAMS, MeterModel
from cyberpunks.a_contoare.train import DETERMINISTIC, FAMILY_TO_Y, LCL_CLASSES
from cyberpunks.common.paths import DATA_INTERIM, REPORTS

DB = DATA_INTERIM / "A" / "optuna.db"
OUT = REPORTS / "A" / "tuning_optuna.json"
N_JOBS = 6
KEYS = ("learning_rate", "num_leaves", "min_child_samples", "subsample", "colsample_bytree", "reg_lambda", "class_weight")


def space(trial: optuna.Trial) -> dict:
    return {
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.1, log=True),
        "num_leaves": trial.suggest_int("num_leaves", 15, 127, log=True),
        "min_child_samples": trial.suggest_int("min_child_samples", 10, 300, log=True),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.4, 1.0),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 30.0, log=True),
        "class_weight": trial.suggest_categorical("class_weight", ["balanced", "none"]),
    }


def _params(p: dict) -> dict:
    p = {**p, "n_jobs": N_JOBS}
    if p.get("class_weight") == "none":
        p["class_weight"] = None
    return p


def subtle_pr_auc(df: pd.DataFrame, score: np.ndarray) -> float:
    subtle = ~(df["kind"].isin(OBVIOUS_KINDS) & (df["problem"] == 1)).to_numpy()
    return M.pr_auc(df["problem"].to_numpy()[subtle], score[subtle])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=30)
    a = ap.parse_args(argv)
    np.seterr(all="ignore")
    MeterModel.save = lambda self, *a, **k: None
    temp = X.london_temperature()
    base, extra = X.base_samples(temp), X.extra_train_samples(temp)
    tr = pd.concat([base[base.split == "train"], extra], ignore_index=True)
    ca, te = (base[base.split == s].reset_index(drop=True) for s in ("cal", "test"))
    feats = list(F.ALL_FEATURES)

    fit_idx, val_idx = next(GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=7).split(tr, groups=tr["household"]))
    t_fit, t_val = tr.iloc[fit_idx].reset_index(drop=True), tr.iloc[val_idx].reset_index(drop=True)
    # validarea are prevalența de antrenare (50% probleme); o aducem la prevalența din test, ca PR-AUC să fie comparabil
    rng = np.random.default_rng(0)
    keep_prob = t_val["problem"] == 0
    n_prob = int(keep_prob.sum() * 0.05 / 0.95)
    prob_idx = rng.choice(np.flatnonzero(~keep_prob), size=min(n_prob, int((~keep_prob).sum())), replace=False)
    t_val = pd.concat([t_val[keep_prob], t_val.iloc[prob_idx]], ignore_index=True)

    def objective(trial: optuna.Trial) -> float:
        p = _params(space(trial))
        y = t_fit["family"].map(FAMILY_TO_Y).to_numpy()
        m = MeterModel("a-opt", feats, LCL_CLASSES).fit(t_fit, y, params={**DETERMINISTIC, **p}, groups=t_fit["household"].to_numpy())
        trial.set_user_attr("best_iteration", m.meta["best_iteration"])
        return subtle_pr_auc(t_val, m.raw_problem_score(t_val))

    DB.parent.mkdir(parents=True, exist_ok=True)
    study = optuna.create_study(study_name="a_lcl_toate", storage=f"sqlite:///{DB}", direction="maximize",
                                load_if_exists=True, sampler=optuna.samplers.TPESampler(seed=42))
    shipped = {k: LGBM_PARAMS[k] for k in KEYS}
    shipped["class_weight"] = shipped["class_weight"] or "none"
    if not study.trials:
        study.enqueue_trial(shipped)
    left = a.trials - len(study.trials)
    if left > 0:
        study.optimize(objective, n_trials=left, show_progress_bar=False)
    best = study.best_params

    r0 = X.fit_eval(tr, ca, te, feats, _params(shipped))
    r1 = X.fit_eval(tr, ca, te, feats, _params(best))
    ci = X.paired_ci(r0, r1)
    keep = ("subtle_precision_at_k", "subtle_recall_at_k", "subtle_pr_auc", "subtle_precision_at_5pct", "pr_auc")
    out = {
        "trials": len(study.trials), "n_train": len(tr), "households_train": int(tr["household"].nunique()),
        "validation": "20% din gospodăriile de antrenare (întregi), prevalența adusă la 5%; PR-AUC pe problemele subtile",
        "val_subtle_pr_auc": {"livrat": round(study.trials[0].value, 4), "gasit": round(study.best_value, 4)},
        "params_livrat": shipped, "params_gasit": best,
        "test": {"livrat": {k: r0[k] for k in keep}, "gasit": {k: r1[k] for k in keep}, "delta_subtle_pr_auc_ci90": ci},
        "importanta_parametrilor": {k: round(v, 3) for k, v in optuna.importance.get_param_importances(study).items()},
        "istoric": [{"n": t.number, "val": round(t.value, 4)} for t in study.trials if t.value is not None],
        "etichete": "SINTETICE: probleme injectate peste consum real", "note": "experiment pe ramura Eden",
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("val_subtle_pr_auc", "test", "params_gasit")}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    raise SystemExit(main())
