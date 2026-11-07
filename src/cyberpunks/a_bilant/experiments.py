"""Încercările care NU au intrat în model, reproductibile: `reports/bilant/experiments.md`.

    uv run python -m cyberpunks.a_bilant.dataset --pool train2   # lotul cu defecte de contor trase ca la A (~30 s)
    uv run python -m cyberpunks.a_bilant.experiments            # după evaluate (citește ferestrele salvate)

Regula: un model nou se păstrează doar dacă e mai bun pe același test (cele 300 de posturi ale hărții).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

from cyberpunks.a_bilant import diagnose as G
from cyberpunks.a_bilant import features as F
from cyberpunks.a_bilant import normal as N
from cyberpunks.a_bilant import windows as W
from cyberpunks.a_bilant.problems import CLASSES
from cyberpunks.common.paths import DATA_PROCESSED, REPORTS


def score(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    g = G.fit(train)
    d = G.pair_consistency(test, G.decide(g.proba(test), test))
    return f1_score(test["true_class"], d["label"], average=None, labels=list(CLASSES))


def main() -> None:
    base = DATA_PROCESSED / "bilant"
    wtr = pd.read_parquet(base / "windows_train.parquet")
    wte = pd.read_parquet(base / "windows_pop.parquet")
    rows = [("modelul actual (lotul train, clase echilibrate)", score(wtr, wte))]
    # 1. lotul train2: defecte de contor trase ca la A (toate tipurile, ~8% pe an)
    if (base / "train2" / "daily.parquet").exists():
        tr = F.load_pool("train")
        t2 = F.load_pool("train2")
        models = N.fit_pair(tr[tr["clean"] & (tr["hist_days"] > 0)])
        w2 = W.build_windows(t2, W.predict_normal(models, t2), "train2")
        rows.append(("antrenat doar pe train2 (defecte ca la A)", score(w2, wte)))
        rows.append(("antrenat pe train + train2", score(pd.concat([wtr, w2], ignore_index=True), wte)))
    # 2. ponderile claselor: echilibrare parțială sau deloc
    y = wtr["true_class"].map({c: i for i, c in enumerate(CLASSES)}).to_numpy()
    bal = len(y) / (len(CLASSES) * np.maximum(np.bincount(y, minlength=len(CLASSES)), 1))
    for name, pw in (("clase echilibrate la radical", 0.5), ("fără echilibrarea claselor", 0.0)):
        rows.append((name, score(wtr.assign(weight=(bal**pw / bal)[y]), wte)))
    head = "| Varianta | F1 macro | " + " | ".join(CLASSES) + " |"
    md = [
        "# Încercări care nu au intrat în model",
        "",
        "SIMULARE. Același test: ferestrele celor 300 de posturi ale hărții, cu defectele de contor ale firului A. Comanda: `uv run python -m cyberpunks.a_bilant.experiments`.",
        "",
        head,
        "|" + "---|" * (len(CLASSES) + 2),
    ]
    for name, f in rows:
        md.append(f"| {name} | {f.mean():.3f} | " + " | ".join(f"{x:.3f}" for x in f) + " |")
    md += [
        "",
        "Concluzii:",
        "- Lotul `train2` (defecte trase pe tot anul) face din „contor de client” clasa dominantă la antrenare, altfel decât la test, unde defectele lui A au apărut doar în ultimele 60 de zile. Rezultatul e mai slab; nu l-am păstrat.",
        "- Ponderile claselor mută puțin echilibrul dintre „contor de client” și „client la postul greșit”, fără câștig la F1 macro. Am păstrat clasele echilibrate.",
        "- Alte încercări, documentate în `error_analysis.md`: comparația cu normalul fără istoric (doar GIS) și extinderea regulii de pereche, ambele fără câștig.",
        "",
    ]
    (REPORTS / "bilant" / "experiments.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
