"""Experimente de robustețe pentru firul A (intră în reports/A/metrics_full.json și în analiza erorilor).

    uv run python -m cyberpunks.a_contoare.robustness

1. Date lipsă: pe populația demo (10.000 de contoare, adevărul injectat cunoscut), ascundem la întâmplare
   0-70% din zile (zile întregi, ca la un concentrator căzut) și măsurăm precizia@K, PR-AUC și câte contoare
   ajung la "nu sunt sigur" din lipsă de date. Motivul: la 31 dec. 2025, gradul de integrare a contoarelor
   inteligente era 56-67% în zonele Rețele Electrice (vezi memory/12-probleme-reale-ppc-2026.md), deci datele
   incomplete sunt situația normală, nu excepția.
2. SGCC pe timp: features pe ferestre de 365 de zile; antrenare pe ferestre care se termină la 31.10.2015,
   test pe clienți NEVĂZUȚI cu ferestre care se termină la 31.10.2016 (perioadă ulterioară).
"""

from __future__ import annotations

import json
import sys
from datetime import date

import numpy as np
import pandas as pd

from cyberpunks.a_contoare import metrics as M
from cyberpunks.a_contoare.demo import build_population
from cyberpunks.a_contoare.features import DAILY_FEATURES, daily_features, intraday_features
from cyberpunks.a_contoare.lcl import INTRADAY_BASE, RECENT, daily_from_halfhours
from cyberpunks.a_contoare.model import MeterModel
from cyberpunks.a_contoare.validate import check_window
from cyberpunks.common.paths import REPORTS

RATES = (0.0, 0.1, 0.3, 0.5, 0.7)


def _post_peers(daily: np.ndarray, post_ids: np.ndarray) -> np.ndarray:
    peer = np.empty_like(daily)
    for p in np.unique(post_ids):
        m = post_ids == p
        with np.errstate(all="ignore"):
            peer[m] = np.nanmedian(daily[m], axis=0)
    return peer


def missing_data_curve(target: date = date(2025, 7, 8), rates: tuple[float, ...] = RATES, seed: int = 7) -> list[dict]:
    model = MeterModel.load("a-lgbm")
    pop = build_population(target, "robustete")
    y = pop.meters["true_problem"].to_numpy()
    k = M.k_for(len(y))
    rows = []
    rng = np.random.default_rng(seed)
    for rate in rates:
        hh = pop.hh.astype(np.float64).copy()
        if rate > 0:
            mask = rng.random(hh.shape[:2]) < rate  # zile întregi lipsă
            hh[mask] = np.nan
        checks = [check_window(hh[i]) for i in range(len(hh))]
        hh = np.stack([c.hh for c in checks])
        daily = daily_from_halfhours(hh)
        peer = _post_peers(daily, pop.meters["post_id"].to_numpy())
        feats = pd.concat(
            [daily_features(daily, peer), intraday_features(hh[:, -RECENT:], hh[:, -RECENT - INTRADAY_BASE : -RECENT])],
            axis=1,
        )
        pred = model.predict(feats)
        abstain = np.array([c.abstain_reason is not None for c in checks])
        s = pred["score"].to_numpy()
        rows.append(
            {
                "missing_days_share": rate,
                "precision_at_k": round(M.precision_at_k(y, s, k), 4),
                "pr_auc": round(M.pr_auc(y, s), 4),
                "roc_auc": round(M.roc_auc(y, s), 4),
                "brier": round(M.brier(y, s), 4),
                "data_abstain_share": round(float(abstain.mean()), 4),
                "problem_decisions": int((pred["conformal"] == "problem").sum()),
                "unsure_decisions": int((pred["conformal"] == "unsure").sum()),
            }
        )
        print(f"lipsă {rate:.0%}: {rows[-1]}")
    return rows


def sgcc_time_split(window: int = 365) -> dict:
    """SGCC: antrenare pe ferestre până la 31.10.2015, test pe clienți nevăzuți cu ferestre până la 31.10.2016."""
    from cyberpunks.a_contoare.baselines import rule_score
    from cyberpunks.a_contoare.sgcc import load_sgcc, split_customers
    from cyberpunks.a_contoare.train import DETERMINISTIC

    _cons, flag, days, x = load_sgcc()
    split = split_customers(flag)
    out = {}
    feats = {}
    for name, end in (("2015", pd.Timestamp("2015-10-31")), ("2016", pd.Timestamp("2016-10-31"))):
        j = days.get_loc(end)
        xw = x[:, j - window + 1 : j + 1]
        with np.errstate(all="ignore"):
            peer = np.nanmedian(xw, axis=0)
        f = daily_features(xw, peer)
        f["label"], f["split"] = flag, split
        feats[name] = f
    tr = feats["2015"][feats["2015"].split == "train"].reset_index(drop=True)
    ca = feats["2015"][feats["2015"].split == "cal"].reset_index(drop=True)
    te = feats["2016"][feats["2016"].split == "test"].reset_index(drop=True)
    m = MeterModel("a-lgbm-sgcc-time", DAILY_FEATURES, ["normal", "tamper"]).fit(tr, tr["label"].to_numpy(), params=DETERMINISTIC)
    m.calibrate(ca, ca["label"].to_numpy())
    y = te["label"].to_numpy()
    k = M.k_for(len(y))
    s = m.predict(te)["score"].to_numpy()
    out["model"] = {kk: round(v, 4) for kk, v in M.ranking_metrics(y, s, k).items()}
    out["rule"] = {kk: round(v, 4) for kk, v in M.ranking_metrics(y, rule_score(te, zero_col="longest_zero_run",
                                                                                  drop_col="max_drop"), k).items()}
    out["missing_share_train_window"] = round(float(np.isnan(x[:, days.get_loc(pd.Timestamp("2015-10-31")) - window + 1:
                                                              days.get_loc(pd.Timestamp("2015-10-31")) + 1]).mean()), 4)
    out["missing_share_test_window"] = round(float(np.isnan(x[:, -window:]).mean()), 4)
    out["note"] = "fereastră de 365 de zile; antrenare 2014-11..2015-10, test pe clienți nevăzuți 2015-11..2016-10"
    print(f"SGCC pe timp: {out}")
    return out


def run() -> dict:
    np.seterr(all="ignore")
    res = {"missing_data_curve": missing_data_curve(), "sgcc_time_split": sgcc_time_split()}
    path = REPORTS / "A" / "robustness.json"
    path.write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"scris: {path}")
    return res


if __name__ == "__main__":
    run()
    sys.exit(0)
