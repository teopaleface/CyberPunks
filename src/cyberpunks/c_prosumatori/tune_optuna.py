"""Căutarea hiperparametrilor modelelor C cu Optuna (experiment pe ramura Eden).

Toate modelele zilnice C (cuantilele P10/P50/P90, clasificatorul, kWh pierduți) folosesc aceiași parametri
LightGBM (`train.LGB_PARAMS`), deci căutăm un singur set. Optuna vede DOAR perioada de antrenare (< 2025): fiecare
încercare antrenează cuantila P50 pe 4 topologii și o notează cu MAE pe celelalte 2 (3 fold-uri, topologii
nevăzute), pe un eșantion de zile. Testul (2025+, topologia lăsată deoparte) se folosește o singură dată, la
final, cu evaluarea completă din `experiments_extra` (parametrii livrați față de cei găsiți).

    uv run python -m cyberpunks.c_prosumatori.tune_optuna --variant mai_multi_ani --trials 40
"""

from __future__ import annotations

import argparse
import json

import numpy as np
import optuna
import pandas as pd

from cyberpunks.c_prosumatori import experiments_extra as X
from cyberpunks.c_prosumatori import features as F
from cyberpunks.c_prosumatori import train as T
from cyberpunks.common.paths import DATA_INTERIM, REPORTS

DB = DATA_INTERIM / "C" / "optuna.db"
FOLDS = [("rural1", "urban6"), ("rural2", "semiurb4"), ("rural3", "semiurb5")]


def space(trial: optuna.Trial) -> dict:
    return {
        "n_estimators": trial.suggest_int("n_estimators", 200, 1500, step=100),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.15, log=True),
        "num_leaves": trial.suggest_int("num_leaves", 15, 255, log=True),
        "min_child_samples": trial.suggest_int("min_child_samples", 20, 600, log=True),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.4, 1.0),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 30.0, log=True),
    }


def train_set(variant: str) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    split = pd.Timestamp(T.SPLIT_DATE)
    pools = {c: X.load_pool(f"x_{c}", c) for c in X.CITIES}
    for d in pools.values():
        d["date"] = pd.to_datetime(d["date"])
    buc = pools["bucuresti"]
    recent = buc[(buc.date >= "2023-01-01") & (buc.date < split)]
    others = pd.concat([pools[c][pools[c].date < split] for c in X.CITIES if c != "bucuresti"], ignore_index=True)
    return {"baza": recent, "mai_multi_ani": buc[buc.date < split],
            "mai_multe_regiuni": pd.concat([recent, others], ignore_index=True),
            "ani_si_regiuni": pd.concat([buc[buc.date < split], others], ignore_index=True)}[variant], pools


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="baza", choices=["baza", "mai_multi_ani", "mai_multe_regiuni", "ani_si_regiuni"])
    ap.add_argument("--trials", type=int, default=40)
    ap.add_argument("--day-frac", type=float, default=0.25)
    a = ap.parse_args(argv)
    tr, pools = train_set(a.variant)
    feats = list(F.DAILY_FEATURES)
    sample = T.sample_for_oof(tr, min(1.0, a.day_frac * X.BASE_TRAIN_ROWS / len(tr) * 4), seed=11)
    print(f"{a.variant}: {len(tr):,} rânduri de antrenare, eșantion pentru căutare {len(sample):,}", flush=True)

    def objective(trial: optuna.Trial) -> float:
        p = space(trial)
        errs = []
        for held in FOLDS:
            fit, val = sample[~sample.topology.isin(held)], sample[sample.topology.isin(held)]
            m = T.fit_quantile(fit[feats], fit["vmax_day"].to_numpy(), 0.5, **p)
            errs.append(np.abs(val["vmax_day"].to_numpy() - m.predict(val[feats])))
        return float(np.mean(np.concatenate(errs)))

    DB.parent.mkdir(parents=True, exist_ok=True)
    study = optuna.create_study(study_name=f"c_{a.variant}", storage=f"sqlite:///{DB}", direction="minimize",
                                load_if_exists=True, sampler=optuna.samplers.TPESampler(seed=42))
    shipped = {k: T.LGB_PARAMS[k] for k in ("n_estimators", "learning_rate", "num_leaves", "min_child_samples",
                                             "subsample", "colsample_bytree", "reg_lambda")}
    if not study.trials:
        study.enqueue_trial(shipped)
    left = a.trials - len(study.trials)
    if left > 0:
        study.optimize(objective, n_trials=left, show_progress_bar=False)
    best = study.best_params

    # o singură dată pe test: evaluarea completă (toate modelele, calibrarea), livrat față de găsit
    split = pd.Timestamp(T.SPLIT_DATE)
    tests = {f"{c}_2025": pools[c][pools[c].date >= split] for c in X.CITIES}
    orig = dict(T.LGB_PARAMS)
    res = {}
    for name, p in (("livrat", shipped), ("gasit", best)):
        T.LGB_PARAMS.update(p)
        try:
            res[name] = X.lotu_eval(tr, tests, feats)
        finally:
            T.LGB_PARAMS.clear()
            T.LGB_PARAMS.update(orig)
    out = {
        "variant": a.variant, "trials": len(study.trials), "train_rows": len(tr),
        "validation": "MAE pe P50, 3 fold-uri de câte 2 topologii nevăzute, perioada de antrenare (< 2025), eșantion de zile",
        "val_mae_pu": {"livrat": round(study.trials[0].value, 6), "gasit": round(study.best_value, 6)},
        "params_livrat": shipped, "params_gasit": best, "test_2025": res,
        "importanta_parametrilor": {k: round(v, 3) for k, v in optuna.importance.get_param_importances(study).items()},
        "istoric": [{"n": t.number, "val_mae": round(t.value, 6)} for t in study.trials if t.value is not None],
        "etichete": "simulare fizică pe rețele SINTETICE", "note": "experiment pe ramura Eden",
    }
    path = REPORTS / "C" / f"tuning_optuna_{a.variant}.json"
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("val_mae_pu", "params_gasit")}, indent=2, ensure_ascii=False))
    for name, r in res.items():
        print(name, {k: v.get("mae_vmax_pu") for k, v in r.items()}, {k: v.get("pr_auc_exceed") for k, v in r.items()})
    return 0


if __name__ == "__main__":
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    raise SystemExit(main())
