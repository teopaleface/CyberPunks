"""Teste pentru piesele benchmarkului (fără date mari). CatBoost/XGBoost sunt în grupul `bench`: fără ele, se omit."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from cyberpunks.benchmark import common as C


def test_ci90_resamples_whole_groups_and_flags_zero():
    groups = np.repeat(np.arange(20), 5)
    const = C.ci90(lambda i: 0.3, groups, n=200)
    assert const["ci90"] == [0.3, 0.3] and not const["includes_zero"] and const["groups"] == 20
    rng = np.random.default_rng(0)
    noise = rng.normal(size=len(groups))
    res = C.ci90(lambda i: float(noise[i].mean()), groups, n=300)
    assert res["includes_zero"] and res["ci90"][0] < res["delta"] < res["ci90"][1]


def test_ci90_skips_nan_statistics():
    groups = np.arange(10)
    res = C.ci90(lambda i: np.nan if len(set(i)) < 6 else 1.0, groups, n=200)
    assert res["n_boot"] < 200 and res["delta"] == 1.0


def test_cat_meter_model_keeps_meter_interface():
    pytest.importorskip("catboost")
    from cyberpunks.benchmark.contoare import CatMeterModel

    rng = np.random.default_rng(1)
    n = 600
    x = pd.DataFrame({"a": rng.normal(size=n), "b": rng.normal(size=n)})
    y = (x["a"] + 0.5 * rng.normal(size=n) > 1).astype(int).to_numpy()
    x.loc[0, "b"] = np.inf  # CatBoost primește inf ca lipsă
    m = CatMeterModel("t", ["a", "b"], ["normal", "tamper"]).fit(x, y, params={"iterations": 50})
    m.calibrate(x, y)
    out = m.predict(x)
    assert {"score", "raw_score", "conformal", "label"} <= set(out.columns)
    assert out["score"].between(0, 1).all()


def test_xgboost_respects_monotone_constraint():
    pytest.importorskip("xgboost")
    from cyberpunks.benchmark.furtuni import xgb_fit

    rng = np.random.default_rng(2)
    X = pd.DataFrame({"g": rng.uniform(0, 100, 2000), "z": rng.normal(size=2000)})
    y = (rng.uniform(size=2000) < np.where(X["g"] > 60, 0.4, 0.05) + 0.1 * (X["z"] > 0)).astype(int)
    f = xgb_fit(X, y.to_numpy(), ["g", "z"], [1, 0], {"max_depth": 3, "min_child_weight": 1.0, "learning_rate": 0.1, "rounds": 50})
    grid = pd.DataFrame({"g": np.linspace(0, 100, 50), "z": 0.0})
    p = f(grid)
    assert np.all(np.diff(p) >= -1e-7)
