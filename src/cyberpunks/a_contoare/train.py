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
from pathlib import Path

import numpy as np
import pandas as pd

from cyberpunks.a_contoare import lcl, sgcc
from cyberpunks.a_contoare.features import ALL_FEATURES, DAILY_FEATURES
from cyberpunks.a_contoare.model import MeterModel

LCL_CLASSES = ["normal", "faulty", "tamper"]
FAMILY_TO_Y = {"normal": 0, "faulty": 1, "tamper": 2}
DETERMINISTIC = {"deterministic": True, "force_col_wise": True}
# Pragurile conformal (alese pe calibrare, verificate pe test și pe demo; vezi reports/A/error_analysis.md):
# - alpha_normal = 1%: mulțimea de predicție conține "normal" pentru cel puțin ~99% din contoarele normale, deci
#   cel mult ~1% din ele sunt declarate sigur "problemă" (spre echipă). Alte contoare normale pot ajunge totuși
#   la om, prin zona gri sau din lipsă de date: rata reală se măsoară și se raportează separat;
# - alpha_problem = 30%: mulțimea conține "problemă" pentru cel puțin ~70% din problemele reale (acoperire, nu
#   recunoaștere sigură: o parte din ele cad în zona gri și merg la om).
ALPHA_NORMAL = 0.01
ALPHA_PROBLEM = 0.30


def train_lcl(samples: pd.DataFrame | None = None) -> MeterModel:
    s = lcl.build_samples() if samples is None else samples
    tr, ca = s[s.split == "train"].reset_index(drop=True), s[s.split == "cal"].reset_index(drop=True)
    y = tr["family"].map(FAMILY_TO_Y).to_numpy()
    m = MeterModel("a-lgbm", ALL_FEATURES, LCL_CLASSES).fit(tr, y, params=DETERMINISTIC, groups=tr["household"].to_numpy())
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


SIMILAR_REF = Path(__file__).resolve().parents[3] / "data" / "samples" / "A" / "similar_ref.parquet"


def export_similar_ref(samples: pd.DataFrame | None = None, n_normal: int = 1500, seed: int = 42) -> Path:
    """Cazurile "din istoric" pentru explicații: toate problemele din calibrare plus o parte din cele normale."""
    s = lcl.build_samples() if samples is None else samples
    cal = s[s.split == "cal"]
    ref = pd.concat([cal[cal.problem == 1], cal[cal.problem == 0].sample(n=min(n_normal, (cal.problem == 0).sum()),
                                                                         random_state=seed)])
    cols = ["sample_id", "kind", "family", "problem", *ALL_FEATURES]
    ref[cols].reset_index(drop=True).to_parquet(SIMILAR_REF, index=False)
    return SIMILAR_REF


def release() -> list[Path]:
    """Ce intră în git pentru demo: modelul agentului, pachetul de profile și cazurile de referință."""
    import shutil

    from cyberpunks.a_contoare.demo import export_pack
    from cyberpunks.a_contoare.model import MODELS_A, RELEASE_A

    RELEASE_A.mkdir(parents=True, exist_ok=True)
    dst = RELEASE_A / "a-lgbm.joblib"
    shutil.copy2(MODELS_A / "a-lgbm.joblib", dst)
    return [dst, export_pack(), export_similar_ref()]


def main() -> int:
    np.seterr(all="ignore")
    if "--release" in sys.argv:
        for p in release():
            print(f"scris: {p}")
        return 0
    m1 = train_sgcc()
    print(f"{m1.version}: {m1.meta['best_iteration']} arbori, antrenare {m1.meta['n_train']}, calibrare {m1.meta['n_cal']}")
    m2 = train_lcl()
    print(f"{m2.version}: {m2.meta['best_iteration']} arbori, antrenare {m2.meta['n_train']}, calibrare {m2.meta['n_cal']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
