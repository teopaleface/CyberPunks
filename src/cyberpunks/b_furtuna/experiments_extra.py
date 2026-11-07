"""Experiment (ramura Eden): ajută variabilele meteo noi și anii de antrenare în plus la modelul B?

Aceeași schemă ca `experiments.py`: antrenare pe anii de dinainte de 2025, test pe 2025 (an nevăzut), aceleași
fold-uri pe săptămâni și aceeași calibrare izotonică. În plus, pentru fiecare variantă, diferența de PR-AUC față de
modelul de bază cu interval bootstrap pe săptămâni (90%), pe aceleași zile de test: dacă intervalul trece de zero,
câștigul nu se distinge de întâmplare.

    uv run python -m cyberpunks.b_furtuna.extra_weather build
    uv run python -m cyberpunks.b_furtuna.experiments_extra          # reports/B/experiments_extra.json
"""

from __future__ import annotations

import argparse
import json

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import average_precision_score, brier_score_loss
from sklearn.model_selection import GroupKFold

from cyberpunks.b_furtuna import extra_weather, more_years
from cyberpunks.b_furtuna import model as bm
from cyberpunks.b_furtuna.evaluate import TEST_YEAR
from cyberpunks.b_furtuna.features import FEATURE_SPEC
from cyberpunks.common.paths import REPORTS

OUT = REPORTS / "B" / "experiments_extra.json"

# grupuri de variabile noi: (coloană, constrângere monotonă)
GROUPS: dict[str, list[tuple[str, int]]] = {
    "ore_cu_rafale": [("gust_hours_50", 1), ("gust_hours_70", 1)],
    "sol_umed": [("soil_top", 0), ("soil_root", 0), ("soil_root_prev", 0)],
    "presiune": [("pmsl_min", 0), ("pmsl_drop24", 1), ("pmsl_drop6_max", 1)],
    "convectie": [("cape_max", 0), ("cape_max_2d", 0), ("li_min", 0), ("tcwv_max", 0), ("dew_max", 0), ("blh_max", 0)],
    "zapada_strat": [("snow_depth_max", 1)],
    "umiditate": [("rh_mean", 0)],
    "directie_rafala": [("gust_dir_sin", 0), ("gust_dir_cos", 0)],
}
DESC = {
    "ore_cu_rafale": "câte ore cu rafale peste 50 și peste 70 km/h (nu doar maxima zilei)",
    "sol_umed": "umiditatea solului 0-7 și 7-28 cm (copaci smulși mai ușor din sol îmbibat)",
    "presiune": "presiunea minimă și scăderea ei în 6 și 24 de ore (fronturi, cicloni)",
    "convectie": "CAPE și lifted index (GFS), apa precipitabilă, punctul de rouă, stratul limită (furtuni de vară)",
    "zapada_strat": "grosimea stratului de zăpadă",
    "umiditate": "umiditatea relativă medie",
    "directie_rafala": "direcția vântului la ora rafalei maxime",
}


def load() -> pd.DataFrame:
    df = more_years.load_all()  # tabelul livrat 2023-2025, plus 2021-2022 dacă au fost construite
    df = df[~df["wx_missing"]]
    ex = pd.read_parquet(extra_weather.OUT)
    ex["date"] = pd.to_datetime(ex["date"])
    return df.merge(ex, on=["fips", "date"], how="left")


def fit_predict(df: pd.DataFrame, spec: list[tuple[str, int]], train_years: tuple[int, ...]) -> tuple[np.ndarray, pd.DataFrame]:
    feats = [f for f, _ in spec]
    params = {**bm.CLF_PARAMS, "monotone_constraints": [m for _, m in spec]}
    tr = df[df["year"].isin(train_years)].reset_index(drop=True)
    te = df[df["year"] == TEST_YEAR].reset_index(drop=True)
    y_tr = tr["event"].to_numpy()

    def fit(X: pd.DataFrame, y: np.ndarray) -> lgb.Booster:
        return lgb.train(params, lgb.Dataset(X[feats], label=y), num_boost_round=bm.CLF_ROUNDS)

    oof = np.zeros(len(tr))
    for a, b in GroupKFold(5).split(tr, y_tr, bm.week_groups(tr["date"])):
        oof[b] = fit(tr.iloc[a], y_tr[a]).predict(tr.iloc[b][feats])
    cal = IsotonicRegression(out_of_bounds="clip").fit(oof, y_tr)
    return cal.predict(fit(tr, y_tr).predict(te[feats])), te


def paired_bootstrap(te: pd.DataFrame, p_base: np.ndarray, p_new: np.ndarray, n: int = 500, seed: int = 42) -> tuple[float, float]:
    """Interval 90% pentru PR-AUC(nou) - PR-AUC(bază), cu reeșantionare pe săptămâni (zilele apropiate sunt corelate)."""
    y = te["event"].to_numpy()
    wk = bm.week_groups(te["date"])
    uniq = np.unique(wk)
    idx_by_wk = {w: np.flatnonzero(wk == w) for w in uniq}
    rng = np.random.default_rng(seed)
    diffs = []
    for _ in range(n):
        idx = np.concatenate([idx_by_wk[w] for w in rng.choice(uniq, size=len(uniq), replace=True)])
        if y[idx].sum() == 0:
            continue
        diffs.append(average_precision_score(y[idx], p_new[idx]) - average_precision_score(y[idx], p_base[idx]))
    lo, hi = np.percentile(diffs, [5, 95])
    return float(lo), float(hi)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-years", default="2023,2024")
    a = ap.parse_args(argv)
    ty = tuple(int(x) for x in a.train_years.split(","))
    df = load()
    base = list(FEATURE_SPEC)
    variants = [("baza", "modelul livrat", base)]
    variants += [(g, "+ " + DESC[g], base + cols) for g, cols in GROUPS.items()]
    allnew = base + [c for cols in GROUPS.values() for c in cols]
    variants.append(("toate_noi", "+ toate variabilele noi", allnew))
    useful = base + GROUPS["ore_cu_rafale"] + GROUPS["sol_umed"] + GROUPS["presiune"] + GROUPS["convectie"]
    variants.append(("rafale_sol_presiune_convectie", "+ ore cu rafale, sol, presiune, convecție", useful))

    rows, p_base = [], None
    for name, desc, spec in variants:
        p, te = fit_predict(df, spec, ty)
        y = te["event"].to_numpy()
        r = {"varianta": name, "ce": desc, "pr_auc": round(float(average_precision_score(y, p)), 4),
             "brier": round(float(brier_score_loss(y, p)), 4), "n_features": len(spec)}
        if p_base is None:
            p_base = p
        else:
            lo, hi = paired_bootstrap(te, p_base, p)
            r["delta_pr_auc_ci90"] = [round(lo, 4), round(hi, 4)]
        rows.append(r)
        print(f"{name:32s} PR-AUC {r['pr_auc']:.4f} Brier {r['brier']:.4f} {r.get('delta_pr_auc_ci90', '')}", flush=True)
    meta = {"train_years": list(ty), "test_year": TEST_YEAR, "counties": int(df["fips"].nunique()),
            "test_rows": int((df["year"] == TEST_YEAR).sum()), "prevalence_test": round(float(df.loc[df["year"] == TEST_YEAR, "event"].mean()), 4),
            "note": "experiment pe ramura Eden; modelul livrat nu e schimbat"}
    OUT.write_text(json.dumps({"meta": meta, "rows": rows}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
