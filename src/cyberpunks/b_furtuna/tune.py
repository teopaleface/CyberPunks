"""Alegerea hiperparametrilor clasificatorului B DOAR pe anii de antrenare (scoruri out-of-fold, fold-uri pe
săptămâni). Anul de test nu e atins aici, ca să nu-l „învățăm” din greșeală.

    uv run python -m cyberpunks.b_furtuna.tune
Scrie `reports/B/tuning.json` (toate configurațiile, sortate după PR-AUC OOF). Configurația aleasă se trece în
`model.CLF_PARAMS` / `model.CLF_ROUNDS`, cu trimitere la acest fișier.
"""

from __future__ import annotations

import itertools
import json

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss
from sklearn.model_selection import GroupKFold

from cyberpunks.b_furtuna import dataset
from cyberpunks.b_furtuna import model as bm
from cyberpunks.b_furtuna.evaluate import TRAIN_YEARS
from cyberpunks.b_furtuna.features import FEATURES
from cyberpunks.common.paths import REPORTS

OUT = REPORTS / "B" / "tuning.json"
GRID = {
    "num_leaves": [7, 15, 31],
    "min_data_in_leaf": [40, 100],
    "learning_rate": [0.02, 0.04],
    "rounds": [300, 600],
}


def oof_pr_auc(tr: pd.DataFrame, params: dict, rounds: int) -> tuple[float, float]:
    y = tr["event"].to_numpy()
    oof = np.zeros(len(tr))
    for a, b in GroupKFold(5).split(tr, y, bm.week_groups(tr["date"])):
        m = lgb.train(params, lgb.Dataset(tr.iloc[a][FEATURES], label=y[a]), num_boost_round=rounds)
        oof[b] = m.predict(tr.iloc[b][FEATURES])
    return float(average_precision_score(y, oof)), float(brier_score_loss(y, oof))


def main() -> int:
    df = pd.read_parquet(dataset.OUT)
    df["date"] = pd.to_datetime(df["date"])
    tr = df[df["year"].isin(TRAIN_YEARS) & ~df["wx_missing"]].reset_index(drop=True)
    rows = []
    keys = list(GRID)
    for values in itertools.product(*(GRID[k] for k in keys)):
        cfg = dict(zip(keys, values, strict=True))
        params = {**bm.CLF_PARAMS, **{k: v for k, v in cfg.items() if k != "rounds"}}
        ap, brier = oof_pr_auc(tr, params, cfg["rounds"])
        rows.append({**cfg, "oof_pr_auc": round(ap, 4), "oof_brier": round(brier, 4)})
        print(cfg, f"PR-AUC OOF {ap:.4f}")
    rows.sort(key=lambda r: -r["oof_pr_auc"])
    out = {"train_years": list(TRAIN_YEARS), "counties": int(tr["fips"].nunique()), "rows": len(tr),
           "current": {"num_leaves": bm.CLF_PARAMS["num_leaves"], "min_data_in_leaf": bm.CLF_PARAMS["min_data_in_leaf"],
                       "learning_rate": bm.CLF_PARAMS["learning_rate"], "rounds": bm.CLF_ROUNDS},
           "results": rows}
    OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print("cel mai bun:", rows[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
