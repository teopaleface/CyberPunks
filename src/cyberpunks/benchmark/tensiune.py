"""Comparație C: LightGBM, CatBoost, XGBoost și regresie liniară pe aceleași rețele/timp.

Experiment separat, buget fix: 60.000 rânduri train/fold, 300 arbori/model, fără tuning.
Numai regresia medianei, fără calibrare/intervale/clasificator; nu înlocuiește pachetul C.
    uv run --group bench python -m cyberpunks.benchmark.tensiune
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from cyberpunks.benchmark import common as C
from cyberpunks.common.paths import DATA_PROCESSED


def run() -> dict:
    from catboost import CatBoostRegressor
    from lightgbm import LGBMRegressor
    from sklearn.linear_model import LinearRegression
    from xgboost import XGBRegressor

    from cyberpunks.c_prosumatori.features import DAILY_FEATURES
    from cyberpunks.c_prosumatori.train import baseline_x

    path = DATA_PROCESSED / "C" / "x_bucuresti" / "daily_features_x.parquet"
    if not path.exists():
        path = DATA_PROCESSED / "C" / "train" / "daily_features.parquet"
    if path.exists():
        df = pd.read_parquet(path)
    elif (DATA_PROCESSED / "C" / "train" / "daily.parquet").exists():
        from cyberpunks.c_prosumatori.train import load_daily
        df = load_daily("train")
    else:
        raise FileNotFoundError("Pregătește datele C: make c-weather c-sim")
    dates = pd.to_datetime(df.date)
    train = df[(dates >= "2023-01-01") & (dates < "2025-01-01")]
    test = df[dates >= "2025-01-01"]
    parts, folds = [], []
    for topology in sorted(df.topology.unique()):
        tr = train[train.topology != topology]
        tr = tr.sample(n=min(60000, len(tr)), random_state=C.SEED)
        te = test[test.topology == topology]
        assert set(tr.post_id).isdisjoint(te.post_id)
        models = {
            "lightgbm": LGBMRegressor(objective="quantile", alpha=.5, n_estimators=300,
                                      learning_rate=.05, num_leaves=31, max_depth=6, min_child_samples=50,
                                      n_jobs=4, random_state=C.SEED, verbosity=-1),
            "catboost": CatBoostRegressor(loss_function="MAE", iterations=300, depth=6, learning_rate=.05,
                                          random_seed=C.SEED, thread_count=4, verbose=False, allow_writing_files=False),
            "xgboost": XGBRegressor(objective="reg:absoluteerror", n_estimators=300, max_depth=6,
                                    learning_rate=.05, n_jobs=4, random_state=C.SEED),
        }
        out = te[["post_id", "date", "topology", "vmax_day"]].copy()
        out["linear"] = LinearRegression().fit(baseline_x(tr), tr.vmax_day).predict(baseline_x(te))
        times = {}
        for name, model in models.items():
            with C.timer(times, name):
                model.fit(tr[DAILY_FEATURES], tr.vmax_day)
                out[name] = model.predict(te[DAILY_FEATURES])
        folds.append({"topology": topology, "train_rows": len(tr), "test_rows": len(te), "seconds": times})
        parts.append(out)
        print(f"C: {topology} gata", flush=True)
    pred = pd.concat(parts, ignore_index=True)
    y = pred.vmax_day.to_numpy()
    result = {}
    for name in ["linear", "lightgbm", "catboost", "xgboost"]:
        error = np.abs(y - pred[name].to_numpy())
        delta = error - np.abs(y - pred.lightgbm.to_numpy())
        result[name] = {"mae_pu": float(error.mean()), "rmse_pu": float(np.sqrt(np.mean((y-pred[name])**2))),
                        "by_topology_mae": pred.assign(error=error).groupby("topology").error.mean().to_dict(),
                        "delta_mae_vs_lightgbm": C.ci90(lambda i, d=delta: float(d[i].mean()), pred.topology, n=1000)}
    report = {"labels": "SINTETICE, calcul fizic pe topologii SimBench; vreme reală București",
              "protocol": "6 folduri: topologie nevăzută × test din 2025; train 2023-2024; aceleași 60000 "
                          "rânduri/fold și trăsături pentru toate modelele, 300 arbori, fără tuning. "
                          "Regresie mediană; baseline liniar GTI×kW/kVA. Nu se selectează un model nou pe test.",
              "limits": "Buget redus pentru această comparație; nu echivalează cu modelul C calibrat complet. "
                        "Doar 6 topologii pentru bootstrap; IC90 exploratoriu, fără corecție de multiplicitate.",
              "test_rows": len(pred), "folds": folds, "test": result, "environment": C.environment()}
    # Float32 păstrează precizia mult sub 0,001 V; câte un fișier/topologie respectă limita de 5 MB/fișier.
    for column in ["vmax_day", "linear", "lightgbm", "catboost", "xgboost"]:
        pred[column] = pred[column].astype("float32")
    for topology, group in pred.groupby("topology"):
        C.write_predictions(f"tensiune_sim_{topology}_test", group)
    C.write_json("tensiune", report)
    return report


if __name__ == "__main__":
    run()
