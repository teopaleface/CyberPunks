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
