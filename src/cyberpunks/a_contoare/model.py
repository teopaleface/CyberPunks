"""Modelul LightGBM al firului A, cu calibrare și "nu sunt sigur".

Un `MeterModel` conține: clasificatorul LightGBM (binar pentru SGCC, 3 clase pentru Londra: normal / defect /
manipulare), calibrarea Venn-ABERS a scorului de problemă și pragurile conformal. Se salvează cu joblib în
`models/A/` (în afara git); o copie mică pentru demo poate sta în `models/release/A/`.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from cyberpunks.a_contoare.calibration import MondrianConformal, VennAbers
from cyberpunks.common.paths import MODELS, ROOT

MODELS_A = MODELS / "A"
RELEASE_A = MODELS / "release" / "A"
N_JOBS = 4  # mașina e împărțită de 6 fire

LGBM_PARAMS = {
    "n_estimators": 3000,
    "learning_rate": 0.03,
    "num_leaves": 31,
    "min_child_samples": 40,
    "subsample": 0.8,
    "subsample_freq": 1,
    "colsample_bytree": 0.8,
    "reg_lambda": 1.0,
    "class_weight": "balanced",
    "n_jobs": N_JOBS,
    "random_state": 42,
    "verbose": -1,
}


def git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "nogit"


def grouped_split(y: np.ndarray, groups: np.ndarray, test_size: float = 0.15, seed: int = 42,
                  tries: int = 20) -> tuple[np.ndarray, np.ndarray]:
    """Împărțire pe grupuri întregi (de exemplu gospodării), cu toate clasele în ambele părți.

    Încearcă mai multe seed-uri; dacă niciunul nu dă toate clasele, se oprește cu eroare, în loc să amestece
    ferestrele aceleiași gospodării în ambele părți.
    """
    from sklearn.model_selection import GroupShuffleSplit

    classes = np.unique(y)
    for t in range(tries):
        tr, va = next(GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed + t).split(y, y, groups))
        if len(np.unique(y[va])) == len(classes) and len(np.unique(y[tr])) == len(classes):
            return tr, va
    raise ValueError("Nu găsesc o împărțire pe grupuri cu toate clasele în ambele părți.")


@dataclass
class MeterModel:
    model_id: str
    features: list[str]
    classes: list[str]  # de exemplu ["normal", "tamper"] sau ["normal", "faulty", "tamper"]
    clf: lgb.LGBMClassifier | None = None
    calibrator: VennAbers = field(default_factory=VennAbers)
    conformal: MondrianConformal = field(default_factory=MondrianConformal)
    version: str = ""
    meta: dict = field(default_factory=dict)

    # ---------------------------------------------------------------- antrenare
    def fit(self, x: pd.DataFrame, y: np.ndarray, seed: int = 42, params: dict | None = None,
            groups: np.ndarray | None = None) -> MeterModel:
        """Antrenează pe (x, y), cu oprire timpurie pe 15% din antrenare (separat de calibrare și de test).

        `groups` (de exemplu gospodăria): validarea pentru oprirea timpurie ia grupuri întregi, ca ferestrele
        aceleiași gospodării să nu fie și în antrenare, și în validare (altfel oprirea e prea optimistă).
        """
        y = np.asarray(y).astype(int)
        if groups is None:
            tr, va = train_test_split(np.arange(len(y)), test_size=0.15, stratify=y, random_state=seed)
        else:
            tr, va = grouped_split(y, groups, test_size=0.15, seed=seed)
        p = {**LGBM_PARAMS, **(params or {}), "random_state": seed}
        multiclass = len(self.classes) > 2
        self.clf = lgb.LGBMClassifier(objective="multiclass" if multiclass else "binary", **p)
        self.clf.fit(
            x.iloc[tr][self.features],
            y[tr],
            eval_set=[(x.iloc[va][self.features], y[va])],
            eval_metric="multi_logloss" if multiclass else "average_precision",
            callbacks=[lgb.early_stopping(100, verbose=False)],
        )
        self.meta["best_iteration"] = int(self.clf.best_iteration_ or p["n_estimators"])
        self.meta["n_train"] = len(tr)
        self.version = f"{self.model_id}@{git_sha()}"
        return self

    def raw_proba(self, x: pd.DataFrame) -> np.ndarray:
        """Probabilitățile brute pe clase (necalibrate), forma (n, n_clase)."""
        return self.clf.predict_proba(x[self.features], num_iteration=self.clf.best_iteration_)

    def raw_problem_score(self, x: pd.DataFrame) -> np.ndarray:
        """Scorul brut de problemă = 1 - P(normal)."""
        return 1.0 - self.raw_proba(x)[:, 0]

    # ---------------------------------------------------------------- calibrare
    def calibrate(self, x_cal: pd.DataFrame, y_cal_problem: np.ndarray, alpha_normal: float = 0.05,
                  alpha_problem: float = 0.10) -> MeterModel:
        """Calibrare Venn-ABERS și conformal pe setul de calibrare (nevăzut la antrenare)."""
        s = self.raw_problem_score(x_cal)
        self.calibrator = VennAbers().fit(s, y_cal_problem)
        # conformal pe scorul BRUT: funcția de scor e fixată înainte de calibrare, deci garanția split conformal
        # rămâne valabilă (pe scorul calibrat, etichetele de calibrare ar influența propriile scoruri)
        self.conformal = MondrianConformal(alpha_normal=alpha_normal, alpha_problem=alpha_problem).fit(s, y_cal_problem)
        # aceleași praguri, traduse în probabilități calibrate (doar pentru explicații)
        p_thr, _, _ = self.calibrator.predict(np.array([1.0 - self.conformal.q_problem, self.conformal.q_normal]))
        self.meta.update({"n_cal": len(y_cal_problem), "p_threshold_problem": float(p_thr[0]),
                          "p_threshold_normal": float(p_thr[1])})
        return self

    def predict(self, x: pd.DataFrame) -> pd.DataFrame:
        """Scorul calibrat de problemă, intervalul, decizia conformal și clasa de problemă cea mai probabilă."""
        proba = self.raw_proba(x)
        s = 1.0 - proba[:, 0]
        p, p0, p1 = self.calibrator.predict(s)
        out = pd.DataFrame({"raw_score": s, "score": p, "interval_low": p0, "interval_high": p1})
        out["conformal"] = self.conformal.decide(s)
        if proba.shape[1] > 2:
            problem = proba[:, 1:]
            share = problem / np.maximum(problem.sum(axis=1, keepdims=True), 1e-12)
            out["label"] = np.array(self.classes[1:])[problem.argmax(axis=1)]
            for j, c in enumerate(self.classes[1:]):
                out[f"p_{c}"] = p * share[:, j]  # probabilitatea calibrată împărțită proporțional pe tipuri
        else:
            out["label"] = self.classes[1]
            out[f"p_{self.classes[1]}"] = p
        return out

    # ---------------------------------------------------------------- salvare
    def save(self, path: Path | None = None) -> Path:
        path = path or MODELS_A / f"{self.model_id}.joblib"
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path, compress=3)
        return path

    @staticmethod
    def load(model_id: str) -> MeterModel:
        for base in (MODELS_A, RELEASE_A):
            p = base / f"{model_id}.joblib"
            if p.exists():
                return joblib.load(p)
        raise FileNotFoundError(f"Nu găsesc modelul {model_id} în {MODELS_A} sau {RELEASE_A}. Rulează make a-train.")
