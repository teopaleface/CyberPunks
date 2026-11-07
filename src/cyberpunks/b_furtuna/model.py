"""Modelul B: LightGBM pentru P(vârf ≥ 1% din clienți) cu calibrare izotonică, plus cuantilele
P10/P50/P90 ale vârfului procentual în zilele cu eveniment (model în doi pași: „dacă se întâmplă, cât de mare”).

Folosit de `evaluate.py` (antrenare și test) și de `predict.py` (aplicarea în România).
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.model_selection import GroupKFold

from cyberpunks.b_furtuna.features import FEATURES, MONOTONE
from cyberpunks.common.paths import MODELS

MODEL_ID = "b-lgbm-quantile"
# Modelul livrat stă în git (models/release/, comprimat), ca planificatorul să poată rula B fără să refacă datele.
MODEL_PATH = MODELS / "release" / "b_model.joblib"
QUANTILES = (0.1, 0.5, 0.9)
N_THREADS = 4  # mașina e împărțită de 6 fire

CLF_PARAMS = {
    "objective": "binary",
    "learning_rate": 0.04,
    "num_leaves": 15,
    "min_data_in_leaf": 40,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 1,
    "lambda_l2": 1.0,
    "monotone_constraints": MONOTONE,
    "monotone_constraints_method": "advanced",
    "num_threads": N_THREADS,
    "verbose": -1,
    "seed": 42,
}
CLF_ROUNDS = 500

Q_PARAMS = {
    "objective": "quantile",
    "learning_rate": 0.04,
    "num_leaves": 15,
    "min_data_in_leaf": 30,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 1,
    "num_threads": N_THREADS,  # LightGBM nu acceptă constrângeri monotone la obiectivul quantile
    "verbose": -1,
    "seed": 42,
}
Q_ROUNDS = 400


def git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "nogit"


@dataclass
class BModel:
    clf: lgb.Booster
    calibrator: IsotonicRegression
    quantile_models: dict[float, lgb.Booster]
    features: list[str]
    ranges: dict[str, tuple[float, float]]  # intervalul văzut la antrenare (pentru "nu sunt sigur")
    decision_threshold: float  # pragul de la care B recomandă echipă trimisă din timp
    version: str
    train_info: dict = field(default_factory=dict)
    cqr_offset: float = 0.0  # lărgirea conformală a intervalului P10-P90 (scara log), pentru acoperire de 80%
    cases: pd.DataFrame | None = None  # biblioteca de zile istorice (SUA) pentru „cazuri asemănătoare”
    case_scale: dict[str, tuple[float, float]] = field(default_factory=dict)  # media și abaterea pe feature

    # -- predicție ------------------------------------------------------------------------
    def raw_score(self, X: pd.DataFrame) -> np.ndarray:
        return self.clf.predict(X[self.features], raw_score=False)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        return np.clip(self.calibrator.predict(self.raw_score(X)), 0.0, 1.0)

    def quantiles_log(self, X: pd.DataFrame) -> np.ndarray:
        """Cuantilele pe scara log(1 + procent), ordonate, cu lărgirea conformală aplicată la P10 și P90."""
        qs = np.sort(np.column_stack([self.quantile_models[q].predict(X[self.features]) for q in QUANTILES]), axis=1)
        qs[:, 0] -= self.cqr_offset
        qs[:, 2] += self.cqr_offset
        return np.clip(qs, 0, None)

    def predict_quantiles(self, X: pd.DataFrame) -> np.ndarray:
        """Vârful procentual (0-1) dacă are loc evenimentul: coloane P10, P50, P90, ordonate."""
        pct = np.expm1(self.quantiles_log(X)) / 100.0
        return np.clip(pct, 0.01, 1.0)  # condiționat pe eveniment: cel puțin 1%

    def out_of_range(self, X: pd.DataFrame, margin: float = 0.10) -> pd.Series:
        """Pentru fiecare rând, lista features-urilor în afara intervalului de antrenare (cu o marjă)."""
        out = []
        for _, row in X[self.features].iterrows():
            bad = []
            for f in self.features:
                lo, hi = self.ranges[f]
                span = hi - lo
                v = row[f]
                if pd.notna(v) and (v < lo - margin * span or v > hi + margin * span):
                    bad.append(f)
            out.append(bad)
        return pd.Series(out, index=X.index)

    # -- salvare ---------------------------------------------------------------------------
    def save(self, path: Path = MODEL_PATH) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path, compress=3)
        return path

    @staticmethod
    def load(path: Path = MODEL_PATH) -> BModel:
        return joblib.load(path)


def week_groups(dates: pd.Series) -> np.ndarray:
    iso = pd.to_datetime(dates).dt.isocalendar()
    return (iso["year"].astype(int) * 100 + iso["week"].astype(int)).to_numpy()


def fit_classifier(X: pd.DataFrame, y: np.ndarray, rounds: int | None = None) -> lgb.Booster:
    return lgb.train(CLF_PARAMS, lgb.Dataset(X[FEATURES], label=y, free_raw_data=False),
                     num_boost_round=rounds or CLF_ROUNDS)


def oof_scores(X: pd.DataFrame, y: np.ndarray, groups: np.ndarray, n_splits: int = 5) -> np.ndarray:
    """Scoruri out-of-fold, cu fold-uri pe săptămâni (o furtună nu ajunge și în antrenare, și în validare)."""
    oof = np.zeros(len(X))
    for tr, va in GroupKFold(n_splits=n_splits).split(X, y, groups):
        m = fit_classifier(X.iloc[tr], y[tr])
        oof[va] = m.predict(X.iloc[va][FEATURES])
    return oof


def fit_quantiles(X_ev: pd.DataFrame, y_log_pct: np.ndarray, rounds: int | None = None) -> dict[float, lgb.Booster]:
    models = {}
    for q in QUANTILES:
        params = {**Q_PARAMS, "alpha": q}
        models[q] = lgb.train(params, lgb.Dataset(X_ev[FEATURES], label=y_log_pct), num_boost_round=rounds or Q_ROUNDS)
    return models


def best_f1_threshold(y: np.ndarray, p: np.ndarray) -> float:
    grid = np.linspace(0.05, 0.9, 86)
    best, best_t = -1.0, 0.5
    for t in grid:
        pred = p >= t
        tp = np.sum(pred & (y == 1))
        fp = np.sum(pred & (y == 0))
        fn = np.sum(~pred & (y == 1))
        f1 = 2 * tp / max(2 * tp + fp + fn, 1)
        if f1 > best:
            best, best_t = f1, float(t)
    return best_t


def train(df: pd.DataFrame, version: str | None = None) -> tuple[BModel, np.ndarray]:
    """Antrenează pe `df` (rândurile fără vreme lipsă). Întoarce modelul și scorurile OOF calibrate."""
    df = df[~df["wx_missing"]].reset_index(drop=True)
    X, y = df[FEATURES], df["event"].to_numpy()
    oof = oof_scores(X, y, week_groups(df["date"]))
    calibrator = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0).fit(oof, y)
    oof_cal = calibrator.predict(oof)
    clf = fit_classifier(X, y)
    ev = df["event"] == 1
    qmodels = fit_quantiles(df.loc[ev, FEATURES], df.loc[ev, "y_log_pct"].to_numpy())
    cqr = conformal_offset(df[ev].reset_index(drop=True))
    ranges = {f: (float(df[f].min()), float(df[f].max())) for f in FEATURES}
    cases, case_scale = case_library(df)
    model = BModel(
        clf=clf,
        calibrator=calibrator,
        quantile_models=qmodels,
        features=list(FEATURES),
        ranges=ranges,
        decision_threshold=best_f1_threshold(y, oof_cal),
        version=version or f"b-lgbm@{git_sha()}",
        train_info={
            "rows": len(df),
            "events": int(y.sum()),
            "counties": int(df["fips"].nunique()),
            "years": sorted(int(v) for v in df["date"].dt.year.unique()),
            "states": sorted(df["state"].unique().tolist()),
        },
        cases=cases,
        case_scale=case_scale,
        cqr_offset=cqr,
    )
    return model, oof_cal


def conformal_offset(ev_df: pd.DataFrame, coverage: float = 0.8, n_splits: int = 5) -> float:
    """Calibrare conformală a cuantilelor (CQR, Romano et al. 2019): cât lărgim [P10, P90] ca să acopere `coverage`.

    Scorul de neconformitate pe cazurile out-of-fold: max(P10 − y, y − P90). Fold-uri pe săptămâni.
    """
    X, y = ev_df[FEATURES], ev_df["y_log_pct"].to_numpy()
    oof = np.zeros((len(ev_df), len(QUANTILES)))
    for tr, va in GroupKFold(n_splits=n_splits).split(X, y, week_groups(ev_df["date"])):
        ms = fit_quantiles(X.iloc[tr], y[tr])
        oof[va] = np.column_stack([ms[q].predict(X.iloc[va]) for q in QUANTILES])
    oof = np.sort(oof, axis=1)
    scores = np.maximum(oof[:, 0] - y, y - oof[:, 2])
    level = min(1.0, coverage * (1 + 1 / len(scores)))
    return float(max(np.quantile(scores, level), 0.0))


CASE_FEATURES = ["gust_max", "gust_prev", "precip_48h", "precip_7d", "snow_3d", "ice_proxy", "tmax", "srad",
                 "doy_sin", "doy_cos"]


def case_library(df: pd.DataFrame, n_calm: int = 4000, seed: int = 42) -> tuple[pd.DataFrame, dict]:
    """Toate zilele cu eveniment plus un eșantion de zile fără, cu vremea și ce s-a întâmplat."""
    ev = df[df["event"] == 1]
    calm = df[df["event"] == 0]
    calm = calm.sample(min(n_calm, len(calm)), random_state=seed)
    lib = pd.concat([ev, calm])[["fips", "county", "state", "date", "pct_out_max", "event", "customers", *CASE_FEATURES]]
    scale = {f: (float(df[f].mean()), float(df[f].std() or 1.0)) for f in CASE_FEATURES}
    return lib.reset_index(drop=True), scale


def shap_values(model: BModel, X: pd.DataFrame) -> np.ndarray:
    """Contribuțiile SHAP (în log-odds) ale fiecărui feature, pentru clasificator. Ultima coloană e baza."""
    return model.clf.predict(X[model.features], pred_contrib=True)
