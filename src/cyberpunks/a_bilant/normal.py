"""Modelul 1: pierderea normală a fiecărui post, pe zi (kWh), cu interval P10-P90.

LightGBM cu regresie cuantilă (P10, P50, P90) pe încărcare (Σ|P|, Σ P², energia injectată de prosumatori), formula
fizică I²R, cablurile din GIS, vreme și istoricul robust al postului (cuantila 20 și mediana raportului din
ultimele 120 de zile, oprit cu 14 zile înainte). Se antrenează pe zilele curate ale lotului `train` și se testează
pe zilele curate ale lotului `pop` (rețele nevăzute: registrul C, harta).

Metode simple de comparat:
- `procent-fix`: pierderea = un procent fix din energia care trece prin post (mediana din antrenare);
- `fizic-i2r`: pierderea = a · Σ P² · R / U² + b · numărul de contoare (cele mai mici pătrate pe antrenare).
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import lightgbm as lgb
import numpy as np
import pandas as pd

from cyberpunks.a_bilant.features import NORMAL_FEATURES
from cyberpunks.common.paths import MODELS

QUANTILES = (0.1, 0.5, 0.9)
MODEL_DIR = MODELS / "bilant"
PARAMS = {"n_estimators": 500, "learning_rate": 0.04, "num_leaves": 31, "min_child_samples": 40, "subsample": 0.8, "subsample_freq": 1, "colsample_bytree": 0.8, "verbose": -1, "n_jobs": 4}


@dataclass
class NormalModel:
    models: dict[float, lgb.LGBMRegressor]
    conformal: tuple[float, float]  # lărgirea intervalului pe validare (kWh) ca acoperirea P10-P90 să fie 80%

    def predict(self, X: pd.DataFrame) -> pd.DataFrame:
        q = {a: m.predict(X[NORMAL_FEATURES]) for a, m in self.models.items()}
        p50 = q[0.5]
        lo = np.minimum(q[0.1], p50) - self.conformal[0]
        hi = np.maximum(q[0.9], p50) + self.conformal[1]
        return pd.DataFrame({"p10": lo, "p50": p50, "p90": hi}, index=X.index)

    def save(self, name: str = "normal") -> None:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        for a, m in self.models.items():
            m.booster_.save_model(str(MODEL_DIR / f"{name}_q{int(a * 100)}.txt"))
        (MODEL_DIR / f"{name}_conformal.json").write_text(json.dumps({"lo": self.conformal[0], "hi": self.conformal[1], "features": NORMAL_FEATURES}))


class _Booster:
    def __init__(self, path: str) -> None:
        self.b = lgb.Booster(model_file=path)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return self.b.predict(X)


def load(name: str = "normal") -> NormalModel:
    c = json.loads((MODEL_DIR / f"{name}_conformal.json").read_text())
    models = {a: _Booster(str(MODEL_DIR / f"{name}_q{int(a * 100)}.txt")) for a in QUANTILES}
    return NormalModel(models=models, conformal=(c["lo"], c["hi"]))  # type: ignore[arg-type]


def drop_history(df: pd.DataFrame) -> pd.DataFrame:
    """Aceleași rânduri fără istoricul postului (post nou sau contor de bilanț abia montat)."""
    cold = df.copy()
    cold[["hist_p20_ratio", "hist_p50_ratio"]] = np.nan
    cold["hist_days"] = 0.0
    return cold


def fit_pair(train: pd.DataFrame, seed: int = 0) -> dict[str, NormalModel]:
    """Două modele: `warm` (cu istoricul postului) și `cold` (fără istoric)."""
    return {"warm": fit(train, seed), "cold": fit(drop_history(train), seed)}


def predict_any(models: dict[str, NormalModel], X: pd.DataFrame) -> pd.DataFrame:
    """Modelul cu istoric unde postul are cel puțin 21 de zile de istoric, altfel modelul fără istoric."""
    out = models["cold"].predict(drop_history(X))
    warm = X["hist_days"].to_numpy() > 0
    if warm.any():
        out.loc[warm] = models["warm"].predict(X.loc[warm]).to_numpy()
    return out


def fit(train: pd.DataFrame, seed: int = 0) -> NormalModel:
    """Antrenează pe 80% din posturile de antrenare; restul de 20% calibrează intervalul (conformal)."""
    posts = train["post_id"].unique()
    rng = np.random.default_rng(seed)
    val_posts = set(rng.choice(posts, size=max(1, len(posts) // 5), replace=False))
    va = train["post_id"].isin(val_posts)
    models = {}
    for a in QUANTILES:
        m = lgb.LGBMRegressor(objective="quantile", alpha=a, random_state=seed, **PARAMS)
        m.fit(train.loc[~va, NORMAL_FEATURES], train.loc[~va, "short_kwh"])
        models[a] = m
    nm = NormalModel(models=models, conformal=(0.0, 0.0))
    pv = nm.predict(train.loc[va])
    y = train.loc[va, "short_kwh"].to_numpy()
    # conformal pe fiecare parte: cât trebuie lărgit ca 10% să cadă sub și 10% peste
    lo_gap = np.quantile(pv["p10"].to_numpy() - y, 0.9)
    hi_gap = np.quantile(y - pv["p90"].to_numpy(), 0.9)
    nm.conformal = (float(max(lo_gap, 0.0)), float(max(hi_gap, 0.0)))
    # reantrenare pe tot setul de antrenare, cu lărgirea găsită
    for a in QUANTILES:
        m = lgb.LGBMRegressor(objective="quantile", alpha=a, random_state=seed, **PARAMS)
        m.fit(train[NORMAL_FEATURES], train["short_kwh"])
        models[a] = m
    return nm


# ---------------------------------------------------------------------------------------------------------
# metodele simple
# ---------------------------------------------------------------------------------------------------------


@dataclass
class FixedPercent:
    q: tuple[float, float, float]

    @classmethod
    def fit(cls, train: pd.DataFrame) -> FixedPercent:
        r = (train["short_kwh"] / train["abs_kwh"].clip(lower=1e-3)).to_numpy()
        return cls(tuple(float(x) for x in np.quantile(r, QUANTILES)))

    def predict(self, X: pd.DataFrame) -> pd.DataFrame:
        a = X["abs_kwh"].to_numpy()
        return pd.DataFrame({"p10": self.q[0] * a, "p50": self.q[1] * a, "p90": self.q[2] * a}, index=X.index)


@dataclass
class PhysicsI2R:
    coef: np.ndarray
    rel_q: tuple[float, float]  # cuantilele erorii relative (P10, P90)

    @classmethod
    def fit(cls, train: pd.DataFrame) -> PhysicsI2R:
        A = np.stack([train["phys_kwh"].to_numpy(), train["own_est_kwh"].to_numpy()], 1)
        y = train["short_kwh"].to_numpy()
        coef, *_ = np.linalg.lstsq(A, y, rcond=None)
        p = A @ coef
        rel = (y - p) / np.maximum(np.abs(p), 1e-3)
        return cls(coef, (float(np.quantile(rel, 0.1)), float(np.quantile(rel, 0.9))))

    def predict(self, X: pd.DataFrame) -> pd.DataFrame:
        p = self.coef[0] * X["phys_kwh"].to_numpy() + self.coef[1] * X["own_est_kwh"].to_numpy()
        return pd.DataFrame({"p10": p * (1 + self.rel_q[0]), "p50": p, "p90": p * (1 + self.rel_q[1])}, index=X.index)


def interval_metrics(y: np.ndarray, pred: pd.DataFrame) -> dict[str, float]:
    p10, p50, p90 = (pred[c].to_numpy() for c in ("p10", "p50", "p90"))
    err = y - p50

    def pin(q: float, p: np.ndarray) -> float:
        e = y - p
        return float(np.mean(np.maximum(q * e, (q - 1) * e)))

    return {
        "mae_kwh_day": float(np.mean(np.abs(err))),
        "mape_pct": float(np.mean(np.abs(err)) / np.mean(np.abs(y)) * 100),
        "bias_kwh_day": float(np.mean(err)),
        "coverage_p10_p90": float(np.mean((y >= p10) & (y <= p90))),
        "interval_width_kwh_day": float(np.mean(p90 - p10)),
        "pinball_mean": float(np.mean([pin(0.1, p10), pin(0.5, p50), pin(0.9, p90)])),
    }
