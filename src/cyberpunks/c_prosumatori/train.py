"""Antrenarea modelelor C.

- Baseline: regresie liniară a tensiunii maxime zilnice pe (radiația maximă × kW de panouri pe kVA), plus
  regresie logistică pe aceeași variabilă pentru P(tensiune > 1,10 pu).
- Model: LightGBM, regresie cuantilă (P10, P50, P90) a tensiunii maxime zilnice, clasificator pentru
  P(tensiune > 1,10 pu) calibrat izotonic pe predicții făcute pe topologii nevăzute, model pentru kWh
  pierduți și model orar (P10, P50, P90) pentru seria din grafic.

    uv run python -m cyberpunks.c_prosumatori.train        # modelele finale în models/C/
"""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass, field

import joblib
import numpy as np
import pandas as pd

from cyberpunks.c_prosumatori import features as F
from cyberpunks.c_prosumatori import simulate, weather
from cyberpunks.common.paths import DATA_PROCESSED, MODELS

LIMIT = simulate.LIMIT_PU
SPLIT_DATE = pd.Timestamp("2025-01-01").date()  # antrenare înainte, test după (luni nevăzute)
QUANTILES = (0.1, 0.5, 0.9)
MODEL_DIR = MODELS / "C"
LGB_PARAMS = {
    "n_estimators": 500,
    "learning_rate": 0.05,
    "num_leaves": 63,
    "min_child_samples": 200,
    "subsample": 0.8,
    "subsample_freq": 1,
    "colsample_bytree": 0.8,
    "reg_lambda": 1.0,
    "n_jobs": 4,
    "verbose": -1,
}
# Constrângeri monotone (fizica): mai mult soare, mai mulți kW, rețea mai slabă, tensiune de pornire mai mare
# nu pot coborî tensiunea maximă.
MONOTONE_UP = {"v0_est", "v_lin_max", "dv_lin_max", "pvk_max", "gti_max", "sens_pv_pu", "pv_kw_per_kva", "pv_kw"}


def git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:  # noqa: BLE001
        return "nogit"


def load_daily(pool: str = "train", refresh: bool = False) -> pd.DataFrame:
    """Trăsăturile zilnice plus etichetele din simulare, pentru un lot de posturi."""
    base = DATA_PROCESSED / "C" / pool
    cache = base / "daily_features.parquet"
    if cache.exists() and not refresh:
        return pd.read_parquet(cache)
    posts = pd.read_parquet(base / "posts.parquet")
    labels = pd.read_parquet(base / "daily.parquet")
    hw = F.hourly_weather(weather.archive())
    X = F.daily_features(posts, hw)
    df = X.merge(labels, on=["post_id", "date"], how="inner").merge(posts[["post_id", "topology"]], on="post_id")
    df["exceed"] = (df["vmax_day"] > LIMIT).astype(int)
    df.to_parquet(cache)
    return df


def _monotone(cols: list[str]) -> list[int]:
    return [1 if c in MONOTONE_UP else 0 for c in cols]


def fit_quantile(X: pd.DataFrame, y: np.ndarray, alpha: float, monotone: bool = True, **kw):
    import lightgbm as lgb

    # LightGBM nu acceptă constrângeri monotone la obiectivul cuantilă; le folosim doar la clasificator
    params = {**LGB_PARAMS, **kw}
    m = lgb.LGBMRegressor(objective="quantile", alpha=alpha, **params)
    m.fit(X, y)
    return m


def fit_classifier(X: pd.DataFrame, y: np.ndarray, monotone: bool = True, **kw):
    import lightgbm as lgb

    params = {**LGB_PARAMS, **kw}
    if monotone:
        params["monotone_constraints"] = _monotone(list(X.columns))
    m = lgb.LGBMClassifier(objective="binary", **params)
    m.fit(X, y)
    return m


def fit_regressor(X: pd.DataFrame, y: np.ndarray, objective: str = "regression", **kw):
    import lightgbm as lgb

    m = lgb.LGBMRegressor(objective=objective, **{**LGB_PARAMS, **kw})
    m.fit(X, y)
    return m


# ------------------------------------------------------------------------------------------------
# baseline: regula kW/kVA × soare
# ------------------------------------------------------------------------------------------------


def baseline_x(df: pd.DataFrame) -> np.ndarray:
    return (df["gti_max"].to_numpy() / 1000.0 * df["pv_kw_per_kva"].to_numpy()).reshape(-1, 1)


@dataclass
class Baseline:
    """Regresie liniară vmax ~ a + b·(GTI × kW/kVA), intervale din cuantilele reziduurilor, logistică pentru depășire."""

    lin: object = None
    log: object = None
    resid_q: dict = field(default_factory=dict)

    def fit(self, df: pd.DataFrame) -> Baseline:
        from sklearn.linear_model import LinearRegression, LogisticRegression

        x, y = baseline_x(df), df["vmax_day"].to_numpy()
        self.lin = LinearRegression().fit(x, y)
        r = y - self.lin.predict(x)
        self.resid_q = {q: float(np.quantile(r, q)) for q in QUANTILES}
        self.log = LogisticRegression(max_iter=1000).fit(x, df["exceed"].to_numpy())
        return self

    def predict(self, df: pd.DataFrame) -> dict[str, np.ndarray]:
        x = baseline_x(df)
        p50 = self.lin.predict(x)
        out = {f"q{int(q * 100)}": p50 + self.resid_q[q] - self.resid_q[0.5] for q in QUANTILES}
        out["q50"] = p50
        out["p_exceed"] = self.log.predict_proba(x)[:, 1]
        return out


# ------------------------------------------------------------------------------------------------
# modelul zilnic complet (cuantile + clasificator calibrat + kWh pierduți)
# ------------------------------------------------------------------------------------------------


@dataclass
class DailyModel:
    features: list[str]
    quantile_models: dict = field(default_factory=dict)
    clf: object = None
    iso: object = None  # calibrarea izotonică a probabilității
    cqr_margin: float = 0.0  # lărgirea intervalului P10-P90 (conformal), pu
    lost_model: object = None
    monotone: bool = True

    def fit(self, df: pd.DataFrame, calib: pd.DataFrame | None = None) -> DailyModel:
        X, y = df[self.features], df["vmax_day"].to_numpy()
        for q in QUANTILES:
            self.quantile_models[q] = fit_quantile(X, y, q, monotone=self.monotone)
        self.clf = fit_classifier(X, df["exceed"].to_numpy(), monotone=self.monotone)
        self.lost_model = fit_regressor(X, np.log1p(df["lost_kwh_day"].to_numpy()))
        if calib is not None:
            self.calibrate(calib)
        return self

    def calibrate(self, oof: pd.DataFrame) -> None:
        """oof: predicții out-of-fold pe topologii nevăzute (coloanele raw_p, q10, q90, vmax_day, exceed)."""
        from sklearn.isotonic import IsotonicRegression

        self.iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0).fit(oof["raw_p"], oof["exceed"])
        e = np.maximum(oof["q10"] - oof["vmax_day"], oof["vmax_day"] - oof["q90"])
        n = len(e)
        self.cqr_margin = float(np.quantile(e, min(1.0, np.ceil((n + 1) * 0.8) / n)))

    def predict(self, df: pd.DataFrame, calibrated: bool = True) -> dict[str, np.ndarray]:
        X = df[self.features]
        q = {f"q{int(a * 100)}": self.quantile_models[a].predict(X) for a in QUANTILES}
        # cuantilele nu au voie să se încrucișeze
        q10, q50, q90 = np.minimum(q["q10"], q["q50"]), q["q50"], np.maximum(q["q90"], q["q50"])
        raw_p = self.clf.predict_proba(X)[:, 1]
        out = {"q10": q10, "q50": q50, "q90": q90, "raw_p": raw_p}
        if calibrated:
            out["q10"], out["q90"] = q10 - self.cqr_margin, q90 + self.cqr_margin
            out["p_exceed"] = self.iso.predict(raw_p) if self.iso is not None else raw_p
        else:
            out["p_exceed"] = raw_p
        out["lost_kwh"] = np.clip(np.expm1(self.lost_model.predict(X)), 0, None)
        return out


def logo_oof(df: pd.DataFrame, features: list[str], monotone: bool = True, topologies=None) -> pd.DataFrame:
    """Predicții out-of-fold pe topologii nevăzute: fiecare topologie e prezisă de modele care n-au văzut-o."""
    topologies = topologies or sorted(df["topology"].unique())
    parts = []
    for t in topologies:
        tr, te = df[df.topology != t], df[df.topology == t]
        X, y = tr[features], tr["vmax_day"].to_numpy()
        qm = {a: fit_quantile(X, y, a, monotone=monotone) for a in (0.1, 0.9)}
        clf = fit_classifier(X, tr["exceed"].to_numpy(), monotone=monotone)
        parts.append(
            pd.DataFrame(
                {
                    "raw_p": clf.predict_proba(te[features])[:, 1],
                    "q10": qm[0.1].predict(te[features]),
                    "q90": qm[0.9].predict(te[features]),
                    "vmax_day": te["vmax_day"].to_numpy(),
                    "exceed": te["exceed"].to_numpy(),
                    "topology": t,
                }
            )
        )
    return pd.concat(parts, ignore_index=True)


def sample_for_oof(df: pd.DataFrame, frac: float = 0.35, seed: int = 0) -> pd.DataFrame:
    """Un eșantion pe zile (toate posturile) ca să țină calibrarea în câteva minute."""
    days = pd.Series(df["date"].unique())
    keep = set(days.sample(frac=frac, random_state=seed))
    return df[df["date"].isin(keep)]


# ------------------------------------------------------------------------------------------------
# modelul orar (seria din grafic)
# ------------------------------------------------------------------------------------------------


def load_hourly_sample(pool: str = "train", day_frac: float = 0.12, night_frac: float = 0.02, seed: int = 1) -> pd.DataFrame:
    base = DATA_PROCESSED / "C" / pool
    posts = pd.read_parquet(base / "posts.parquet")
    hw = F.hourly_weather(weather.archive())
    rng = np.random.default_rng(seed)
    frames = []
    for _, st in posts.iterrows():
        h = pd.read_parquet(base / "hourly" / f"{st['post_id']}.parquet")
        day = hw["pvk"].to_numpy() > 0
        keep = np.where(day, rng.random(len(hw)) < day_frac, rng.random(len(hw)) < night_frac)
        f = F.hourly_features(st, hw[keep])
        f["vmax"] = h["vmax"].to_numpy()[keep]
        f["post_id"], f["topology"], f["date"] = st["post_id"], st["topology"], hw["date"].to_numpy()[keep]
        frames.append(f)
    return pd.concat(frames)


@dataclass
class HourlyModel:
    features: list[str]
    models: dict = field(default_factory=dict)

    def fit(self, df: pd.DataFrame) -> HourlyModel:
        X, y = df[self.features], df["vmax"].to_numpy()
        for q in QUANTILES:
            self.models[q] = fit_quantile(X, y, q, monotone=False, n_estimators=400)
        return self

    def predict(self, df: pd.DataFrame) -> dict[str, np.ndarray]:
        X = df[self.features]
        q = {a: self.models[a].predict(X) for a in QUANTILES}
        return {"q10": np.minimum(q[0.1], q[0.5]), "q50": q[0.5], "q90": np.maximum(q[0.9], q[0.5])}


# ------------------------------------------------------------------------------------------------
# modelele finale (pentru predict.py)
# ------------------------------------------------------------------------------------------------


@dataclass
class Bundle:
    daily: DailyModel
    hourly: HourlyModel
    baseline: Baseline
    version: str
    trained_on: dict
    ood_ranges: dict  # plajele văzute la antrenare, pentru „nu sunt sigur” pe rețele noi


def train_final(exclude_dates: list[str] | None = None, oof_frac: float = 0.35) -> Bundle:
    t0 = time.perf_counter()
    df = load_daily("train")
    if exclude_dates:
        ex = set()
        for d in exclude_dates:
            c = pd.Timestamp(d)
            ex |= {(c + pd.Timedelta(days=k)).date() for k in range(-3, 4)}
        df = df[~df["date"].isin(ex)]
    feats = F.DAILY_FEATURES
    oof = logo_oof(sample_for_oof(df, oof_frac), feats)
    daily = DailyModel(features=feats).fit(df, calib=oof)
    hs = load_hourly_sample("train")
    if exclude_dates:
        hs = hs[~hs["date"].isin(ex)]
    hourly = HourlyModel(features=F.HOURLY_FEATURES).fit(hs)
    base = Baseline().fit(df)
    posts = pd.read_parquet(DATA_PROCESSED / "C" / "train" / "posts.parquet")
    ood = {c: [float(posts[c].min()), float(posts[c].max())] for c in F.STATIC}
    version = f"c-lgbm@{git_sha()}"
    b = Bundle(daily=daily, hourly=hourly, baseline=base, version=version, ood_ranges=ood,
               trained_on={"rows_daily": len(df), "rows_hourly": len(hs), "posts": int(df.post_id.nunique()),
                           "excluded_dates": exclude_dates or [], "seconds": round(time.perf_counter() - t0, 1)})
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(b, MODEL_DIR / "bundle.joblib", compress=3)
    (MODEL_DIR / "bundle.json").write_text(json.dumps({"version": version, "cqr_margin": daily.cqr_margin, **b.trained_on}, indent=2))
    return b


RELEASE_DIR = MODELS / "release" / "C"


def load_bundle() -> Bundle:
    """Modelul antrenat local (models/C) sau, într-o clonă curată, versiunea din git (models/release/C)."""
    for d in (MODEL_DIR, RELEASE_DIR):
        if (d / "bundle.joblib").exists():
            return joblib.load(d / "bundle.joblib")
    raise FileNotFoundError("Lipsește modelul C: rulați `make c-sim c-population c-train` (sau `make c-all`).")


if __name__ == "__main__":
    import argparse

    from cyberpunks.common.config import load

    ap = argparse.ArgumentParser()
    ap.add_argument("--exclude", nargs="*", default=None, help="date excluse (±3 zile), de exemplu ziua demo")
    a = ap.parse_args()
    exclude = a.exclude
    if exclude is None:
        d = str(load("scenarios")["scenarios"]["demo-vara"]["date"])
        exclude = [d] if d and not d.startswith("TBD") else ["2025-07-08"]  # data demo aleasă de firul B
    # apelăm prin modulul importat, ca obiectele salvate să trimită la cyberpunks.c_prosumatori.train, nu la __main__
    import importlib

    b = importlib.import_module("cyberpunks.c_prosumatori.train").train_final(exclude)
    print(b.version, b.trained_on, "cqr", round(b.daily.cqr_margin, 4))
