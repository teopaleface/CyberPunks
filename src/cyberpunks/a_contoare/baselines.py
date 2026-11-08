"""Baseline-urile, cu care se compară modelul pe același set de test.

1. Regula simplă, de tip VEE (ce fac azi utilitățile): contorul e suspect dacă are consum zero cel puțin N zile la
   rând SAU dacă a scăzut cu cel puțin 50% față de propriul istoric. Scorul de clasament e
   max(zile_cu_zero / N, scădere / 0,5); scorul >= 1 înseamnă "regula s-a declanșat".
2. IsolationForest pe aceleași features: detecție de anomalii fără etichete (antrenat pe tot setul de antrenare,
   fără să se uite la etichete). Valorile lipsă se completează cu mediana din antrenare.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

RULE_ZERO_DAYS = 7  # N: o săptămână întreagă cu zero (regula VEE "consecutive zeros", la nivel de zi)
RULE_DROP = 0.5  # scădere de cel puțin 50% față de propriul istoric


def rule_score(feats: pd.DataFrame, *, zero_col: str = "zero_run_recent", drop_col: str = "recent_vs_base") -> np.ndarray:
    """Scorul regulii simple. `drop_col` e un raport (recent/istoric) sau, pentru 'max_drop', direct scăderea."""
    zero = feats[zero_col].to_numpy(dtype=float)
    if drop_col == "max_drop":
        drop = feats[drop_col].to_numpy(dtype=float)
    else:
        drop = 1.0 - feats[drop_col].to_numpy(dtype=float)
    s = np.fmax(np.nan_to_num(zero, nan=0.0) / RULE_ZERO_DAYS, np.nan_to_num(drop, nan=0.0) / RULE_DROP)
    return np.clip(s, 0.0, 10.0)


@dataclass
class IForestBaseline:
    features: list[str]
    seed: int = 42
    medians: pd.Series = field(default_factory=pd.Series)
    model: IsolationForest | None = None

    def fit(self, feats: pd.DataFrame) -> IForestBaseline:
        x = feats[self.features].astype(float)
        self.medians = x.median()
        self.model = IsolationForest(n_estimators=300, max_samples=min(4096, len(x)), random_state=self.seed, n_jobs=4)
        self.model.fit(x.fillna(self.medians).to_numpy())
        return self

    def score(self, feats: pd.DataFrame) -> np.ndarray:
        x = feats[self.features].astype(float).fillna(self.medians).to_numpy()
        return -self.model.score_samples(x)  # mai mare = mai anormal


VEE_DEFAULTS = {"spike_days": 3.0, "spike_slots": 10.0}


def vee_full_score(feats: pd.DataFrame, *, window_wide: bool = False, spike_days: float | None = None,
                   spike_slots: float | None = None) -> np.ndarray:
    """Regula VEE completă (al doilea baseline, mai puternic decât regula simplă).

    Verificări, după familiile VEE din Oracle Utilities MDM și tutorialul Oncor/ERCOT: zero la rând >= 7 zile;
    aceeași valoare >= 7 zile; goluri (>= 25% din ultimele 4 săptămâni, sau un gol >= 14 zile pe toată fereastra);
    citiri negative; salturi (zile și intervale de 30 de minute, pragurile alese pe setul de calibrare); scădere
    >= 50%. Clasamentul: câte verificări s-au declanșat, apoi cât de departe e cea mai mare peste prag.
    `window_wide=True` (SGCC, etichetă pe toată perioada) folosește variantele pe toată fereastra.
    """
    spike_days = VEE_DEFAULTS["spike_days"] if spike_days is None else spike_days
    spike_slots = VEE_DEFAULTS["spike_slots"] if spike_slots is None else spike_slots

    def col(name: str) -> np.ndarray:
        return np.nan_to_num(feats[name].to_numpy(dtype=float), nan=0.0) if name in feats else np.zeros(len(feats))

    drop = col("max_drop") if window_wide else 1.0 - np.nan_to_num(feats["recent_vs_base"].to_numpy(dtype=float), nan=1.0)
    parts = np.vstack(
        [
            col("longest_zero_run" if window_wide else "zero_run_recent") / RULE_ZERO_DAYS,
            col("longest_flat_run") / 7.0,
            (col("longest_gap") / 14.0) if window_wide else (col("missing_recent") / 0.25),
            np.where(col("negative_count") > 0, 1.0, 0.0),
            col("spike_count") / spike_days,
            col("spike_slot_count") / spike_slots,
            drop / RULE_DROP,
        ]
    )
    fired = (parts >= 1.0).sum(axis=0)
    return fired + 0.1 * np.clip(parts.max(axis=0), 0.0, 10.0) / 10.0


def tune_vee(feats_cal: pd.DataFrame, y_cal: np.ndarray, k: int, *, window_wide: bool = False) -> dict[str, float]:
    """Pragurile de salt pentru regula VEE, alese pe calibrare (îi dăm regulii cea mai bună șansă)."""
    from cyberpunks.a_contoare.metrics import pr_auc, precision_at_k

    best, best_key = None, (-1.0, -1.0)
    for sd in (1.0, 3.0, 10.0, 30.0):
        for ss in (3.0, 10.0, 30.0, 100.0):
            sc = vee_full_score(feats_cal, window_wide=window_wide, spike_days=sd, spike_slots=ss)
            key = (precision_at_k(y_cal, sc, k), pr_auc(y_cal, sc))
            if key > best_key:
                best, best_key = {"spike_days": sd, "spike_slots": ss}, key
    return best
