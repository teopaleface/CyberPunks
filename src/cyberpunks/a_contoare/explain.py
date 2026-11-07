"""Explicabilitate: de ce a semnalat modelul un contor.

- `top_factors`: valorile SHAP (TreeExplainer, exacte pentru arbori) pentru clasa prezisă (defect sau manipulare);
  păstrăm factorii care împing spre problemă, cu explicația în cuvinte simple (`label_ro` din features.py).
- `SimilarCases`: cele mai apropiate cazuri "din istoric" (setul de calibrare, cu rezultatul cunoscut), după
  features standardizate robust. Rezultatul lor ("contor oprit", "manipulare confirmată") ajută omul să decidă.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import shap
from sklearn.neighbors import NearestNeighbors

from cyberpunks.a_contoare.features import label_ro
from cyberpunks.a_contoare.inject import KIND_LABEL_RO, KIND_OUTCOME
from cyberpunks.a_contoare.model import MeterModel


def shap_values(model: MeterModel, x: pd.DataFrame) -> np.ndarray:
    """SHAP pe clase: forma (n, n_features, n_clase), în spațiul log-odds al modelului."""
    explainer = shap.TreeExplainer(model.clf.booster_)
    sv = explainer.shap_values(x[model.features])
    sv = np.asarray(sv)
    if sv.ndim == 2:  # binar: o singură matrice pentru clasa pozitivă
        sv = np.stack([-sv, sv], axis=2)
    elif sv.shape[0] == len(model.classes) and sv.shape[1] == len(x):  # format vechi: (clase, n, features)
        sv = np.transpose(sv, (1, 2, 0))
    return sv


def top_factors(model: MeterModel, x: pd.DataFrame, labels: list[str], k: int = 5) -> list[list[dict]]:
    """Pentru fiecare rând: până la k factori (feature, label_ro, valoare, contribuție SHAP) spre clasa prezisă."""
    sv = shap_values(model, x)
    out = []
    for i, lab in enumerate(labels):
        c = model.classes.index(lab) if lab in model.classes else len(model.classes) - 1
        contrib = sv[i, :, c]
        order = np.argsort(-contrib)
        rows = []
        for j in order:
            if len(rows) == k or (contrib[j] <= 0 and rows):
                break
            f = model.features[j]
            v = x.iloc[i][f]
            v = None if pd.isna(v) else float(v)
            if v is None and j != order[-1]:
                continue  # un feature fără valoare nu se poate explica unui tehnician
            rows.append({"feature": f, "label_ro": label_ro(f, v), "value": None if v is None else round(v, 4),
                         "contribution": round(float(contrib[j]), 4)})
        out.append(rows)
    return out


@dataclass
class SimilarCases:
    features: list[str]
    ref: pd.DataFrame  # cazurile de referință (calibrare), cu 'sample_id', 'kind', 'problem'
    center: np.ndarray
    scale: np.ndarray
    nn: NearestNeighbors
    typical_dist: float

    @classmethod
    def fit(cls, ref: pd.DataFrame, features: list[str]) -> SimilarCases:
        x = ref[features].astype(float).to_numpy()
        center = np.nanmedian(x, axis=0)
        q75, q25 = np.nanpercentile(x, [75, 25], axis=0)
        scale = np.where((q75 - q25) > 1e-9, q75 - q25, 1.0)
        z = cls._z(x, center, scale)
        nn = NearestNeighbors(n_neighbors=8).fit(z)
        d, _ = nn.kneighbors(z[: min(2000, len(z))], n_neighbors=2)
        return cls(features, ref.reset_index(drop=True), center, scale, nn, float(np.median(d[:, 1])) or 1.0)

    @staticmethod
    def _z(x: np.ndarray, center: np.ndarray, scale: np.ndarray) -> np.ndarray:
        z = (x - center) / scale
        return np.clip(np.nan_to_num(z, nan=0.0), -10, 10)

    def query(self, x: pd.DataFrame, k: int = 3) -> list[list[dict]]:
        z = self._z(x[self.features].astype(float).to_numpy(), self.center, self.scale)
        d, idx = self.nn.kneighbors(z, n_neighbors=8)
        out = []
        for di, ii in zip(d, idx, strict=True):
            rows = []
            for dist, j in zip(di, ii, strict=True):
                r = self.ref.iloc[j]
                kind = r["kind"] if r["problem"] == 1 else "none"
                rows.append(
                    {
                        "case_id": str(r["sample_id"]),
                        "outcome": KIND_OUTCOME.get(kind, "normal"),
                        "similarity": round(float(np.exp(-dist / (2 * self.typical_dist))), 3),
                        "note_ro": f"{KIND_LABEL_RO.get(kind, 'fără problemă')} (caz din istoric, date sintetice)",
                    }
                )
                if len(rows) == k:
                    break
            out.append(rows)
        return out
