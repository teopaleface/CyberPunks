"""Antrenarea modelelor firului A (reproductibilă: seed-uri fixe, LightGBM determinist).

    uv run python -m cyberpunks.a_contoare.train

- `a-lgbm`: modelul folosit de agent. LightGBM cu 3 clase (normal / defect / manipulare) pe eșantioanele din
  Londra (consum real, probleme injectate), cu features zilnice și din citirile la 30 de minute.
- `a-lgbm-sgcc`: același tip de model, binar (normal / furt), pe SGCC cu etichete reale de furt; doar features
  zilnice (SGCC are o citire pe zi). Arată cât valorează aceleași features pe etichete reale.
Ambele se calibrează pe setul de calibrare (nevăzut la antrenare) și se salvează în models/A/.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from cyberpunks.a_contoare import lcl, sgcc
from cyberpunks.a_contoare.features import ALL_FEATURES, DAILY_FEATURES
from cyberpunks.a_contoare.model import MeterModel

LCL_CLASSES = ["normal", "faulty", "tamper"]
FAMILY_TO_Y = {"normal": 0, "faulty": 1, "tamper": 2}
DETERMINISTIC = {"deterministic": True, "force_col_wise": True}
# Pragurile conformal: alpha mic pentru "normal" (rar declarăm normal un contor cu problemă reală),
# alpha mai mare pentru "problemă" (acceptăm să ratăm o parte, ca să nu trimitem totul la om).
ALPHA_NORMAL = 0.05
ALPHA_PROBLEM = 0.20


def train_lcl(samples: pd.DataFrame | None = None) -> MeterModel:
    s = lcl.build_samples() if samples is None else samples
    tr, ca = s[s.split == "train"].reset_index(drop=True), s[s.split == "cal"].reset_index(drop=True)
    y = tr["family"].map(FAMILY_TO_Y).to_numpy()
    m = MeterModel("a-lgbm", ALL_FEATURES, LCL_CLASSES).fit(tr, y, params=DETERMINISTIC)
    m.calibrate(ca, ca["problem"].to_numpy(), alpha_normal=ALPHA_NORMAL, alpha_problem=ALPHA_PROBLEM)
    m.meta.update({"dataset": "Low Carbon London + probleme injectate (sintetic)", "n_samples_train": len(tr)})
    m.save()
    return m


def train_sgcc(feats: pd.DataFrame | None = None) -> MeterModel:
    f = sgcc.build_features() if feats is None else feats
    tr, ca = f[f.split == "train"].reset_index(drop=True), f[f.split == "cal"].reset_index(drop=True)
    m = MeterModel("a-lgbm-sgcc", DAILY_FEATURES, ["normal", "tamper"]).fit(tr, tr["label"].to_numpy(), params=DETERMINISTIC)
    m.calibrate(ca, ca["label"].to_numpy(), alpha_normal=ALPHA_NORMAL, alpha_problem=ALPHA_PROBLEM)
    m.meta.update({"dataset": "SGCC (etichete reale de furt)", "n_samples_train": len(tr)})
    m.save()
    return m


def main() -> int:
    np.seterr(all="ignore")
    m1 = train_sgcc()
    print(f"{m1.version}: {m1.meta['best_iteration']} arbori, antrenare {m1.meta['n_train']}, calibrare {m1.meta['n_cal']}")
    m2 = train_lcl()
    print(f"{m2.version}: {m2.meta['best_iteration']} arbori, antrenare {m2.meta['n_train']}, calibrare {m2.meta['n_cal']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
