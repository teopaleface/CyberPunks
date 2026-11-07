"""Regresie logistică vs LightGBM pentru firul A (contoare), pe aceleași împărțiri ca echipa.
# Rulare (din rădăcina repo-ului, pe main): uv run python reports/lr_vs_lgbm/compare_a.py [sgcc|london|all]
# Cere datele A (make a-data) sau, pentru bilanț, ferestrele din make bilant-data bilant-eval.

- Aceleași features, același lot de antrenare, același lot de test (nevăzut), aceleași metrici (metrics.py).
- LR: completare cu mediana + indicator de lipsă, apoi (v1) StandardScaler sau (v2) QuantileTransformer->normal,
  L2, class_weight="balanced". C se alege pe lotul de CALIBRARE (nu pe test), după PR-AUC.
- Londra: 3 clase ca la LightGBM, scorul = 1 - P(normal).
- Verdict: bootstrap pereche (pe gospodării la Londra) pentru diferența LR - LGBM.
"""

from __future__ import annotations

import json
import sys
import time

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import QuantileTransformer, StandardScaler

from cyberpunks.a_contoare import lcl, sgcc
from cyberpunks.a_contoare import metrics as M
from cyberpunks.a_contoare.evaluate import OBVIOUS_KINDS
from cyberpunks.a_contoare.features import ALL_FEATURES, DAILY_FEATURES
from cyberpunks.a_contoare.train import FAMILY_TO_Y, train_lcl, train_sgcc

C_GRID = [0.001, 0.01, 0.1, 1.0, 10.0]
N_BOOT = 1000


def lr_pipe(kind: str, c: float):
    pre = StandardScaler() if kind == "std" else QuantileTransformer(output_distribution="normal", n_quantiles=1000,
                                                                     subsample=200_000, random_state=0)
    return make_pipeline(SimpleImputer(strategy="median", add_indicator=True), pre,
                         LogisticRegression(C=c, class_weight="balanced", max_iter=3000))


def clean(x: pd.DataFrame, feats: list[str]) -> pd.DataFrame:
    return x[feats].replace([np.inf, -np.inf], np.nan).astype(float)


def problem_score(pipe, x) -> np.ndarray:
    return 1.0 - pipe.predict_proba(x)[:, 0]


def fit_lr(kind, xtr, ytr, xca, yca_problem):
    best = None
    for c in C_GRID:
        p = lr_pipe(kind, c).fit(xtr, ytr)
        ap = M.pr_auc(yca_problem, problem_score(p, xca))
        print(f"    LR-{kind} C={c:<6} PR-AUC(calibrare)={ap:.4f}", flush=True)
        if best is None or ap > best[0]:
            best = (ap, c, p)
    return best[2], best[1]


def all_metrics(y, s, k, value=None):
    r = {"precision_at_k": M.precision_at_k(y, s, k), "recall_at_k": M.recall_at_k(y, s, k),
         "pr_auc": M.pr_auc(y, s), "roc_auc": M.roc_auc(y, s)}
    if value is not None:
        r["value_at_k_lei"] = M.value_at_k(value, s, k)
    return r


def paired_boot(y, s_a, s_b, k_share, groups=None, n=N_BOOT, seed=0, value=None):
    """Bootstrap pereche: aceleași eșantioane pentru ambele modele; întoarce IC 95% pentru diferența a - b."""
    rng = np.random.default_rng(seed)
    y, s_a, s_b = map(np.asarray, (y, s_a, s_b))
    if groups is None:
        members = None
        n_units = len(y)
    else:
        uniq, inv = np.unique(groups, return_inverse=True)
        order = np.argsort(inv, kind="stable")
        bounds = np.searchsorted(inv[order], np.arange(len(uniq) + 1))
        members = [order[bounds[g]:bounds[g + 1]] for g in range(len(uniq))]
        n_units = len(uniq)
    d = {"pr_auc": [], "precision_at_k": [], "roc_auc": []}
    for b in range(n):
        pick = rng.integers(0, n_units, n_units)
        idx = pick if members is None else np.concatenate([members[g] for g in pick])
        yy = y[idx]
        if yy.min() == yy.max():
            continue
        kk = max(1, round(len(yy) * k_share))
        d["pr_auc"].append(M.pr_auc(yy, s_a[idx]) - M.pr_auc(yy, s_b[idx]))
        d["roc_auc"].append(M.roc_auc(yy, s_a[idx]) - M.roc_auc(yy, s_b[idx]))
        d["precision_at_k"].append(M.precision_at_k(yy, s_a[idx], kk, seed=b) - M.precision_at_k(yy, s_b[idx], kk, seed=b))
        if value is not None:
            vv = np.asarray(value, dtype=float)[idx]
            d.setdefault("value_at_k_lei", []).append(M.value_at_k(vv, s_a[idx], kk, seed=b)
                                                      - M.value_at_k(vv, s_b[idx], kk, seed=b))
    out = {}
    for key, v in d.items():
        v = np.asarray(v)
        out[key] = {"mean_diff": float(v.mean()), "ci95": [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))],
                    "p_lr_better": float((v > 0).mean())}
    return out


def run_set(name, tr, ca, te, feats, y_tr, y_ca_problem, y_te, lgbm_score_te, lgbm_score_tr, y_tr_problem,
            groups_te=None, value_te=None, subsets=None):
    print(f"\n=== {name}: train {len(tr)}, cal {len(ca)}, test {len(te)}, prevalență test {y_te.mean():.4f}", flush=True)
    xtr, xca, xte = clean(tr, feats), clean(ca, feats), clean(te, feats)
    k_share = M.BUDGET_SHARE
    k = M.k_for(len(y_te))
    res = {"n_train": len(tr), "n_test": len(te), "prevalence_test": float(y_te.mean()), "k": k,
           "models": {}, "train_vs_test": {}, "paired_bootstrap_lr_minus_lgbm": {}}
    scores = {"lgbm": lgbm_score_te}
    res["models"]["lgbm"] = all_metrics(y_te, lgbm_score_te, k, value_te)
    res["train_vs_test"]["lgbm"] = {"pr_auc_train": M.pr_auc(y_tr_problem, lgbm_score_tr),
                                     "pr_auc_test": res["models"]["lgbm"]["pr_auc"]}
    for kind in ("std", "quantile"):
        t0 = time.perf_counter()
        pipe, c = fit_lr(kind, xtr, y_tr, xca, y_ca_problem)
        s = problem_score(pipe, xte)
        key = f"lr_{kind}"
        scores[key] = s
        res["models"][key] = {**all_metrics(y_te, s, k, value_te), "C": c, "fit_seconds": time.perf_counter() - t0}
        res["train_vs_test"][key] = {"pr_auc_train": M.pr_auc(y_tr_problem, problem_score(pipe, xtr)),
                                     "pr_auc_test": res["models"][key]["pr_auc"]}
        res["paired_bootstrap_lr_minus_lgbm"][key] = paired_boot(y_te, s, lgbm_score_te, k_share, groups_te,
                                                                 value=value_te)
    for m, r in res["models"].items():
        print(f"  {m:12s} P@K={r['precision_at_k']:.3f}  PR-AUC={r['pr_auc']:.3f}  ROC-AUC={r['roc_auc']:.3f}"
              + (f"  valoare@K={r['value_at_k_lei']:.0f} lei" if 'value_at_k_lei' in r else ""), flush=True)
    if subsets:
        res["subsets"] = {}
        for sname, mask in subsets.items():
            ys = y_te[mask]
            ks = M.k_for(int(mask.sum()))
            sub = {"n": int(mask.sum()), "models": {m: all_metrics(ys, s[mask], ks) for m, s in scores.items()},
                   "paired_bootstrap_lr_minus_lgbm": {
                       m: paired_boot(ys, sc[mask], scores["lgbm"][mask], k_share,
                                      None if groups_te is None else groups_te[mask])
                       for m, sc in scores.items() if m != "lgbm"}}
            res["subsets"][sname] = sub
            for m, r in sub["models"].items():
                print(f"  [{sname}] {m:12s} P@K={r['precision_at_k']:.3f}  PR-AUC={r['pr_auc']:.3f}  ROC-AUC={r['roc_auc']:.3f}")
    return res


def main() -> int:
    np.seterr(all="ignore")
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    out = {}
    if which in ("all", "sgcc"):
        out["sgcc"] = run_sgcc()
    if which in ("all", "london"):
        out["london"] = run_london()
    path = f"reports/lr_vs_lgbm/results_a_{which}.json"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    print(f"\nscris: {path}")
    return 0


def run_sgcc():
    # SGCC (etichete reale de furt), binar, doar features zilnice
    f = sgcc.build_features()
    s_tr, s_ca, s_te = (f[f.split == x].reset_index(drop=True) for x in ("train", "cal", "test"))
    m_s = train_sgcc(f)
    return run_set("SGCC (furt real)", s_tr, s_ca, s_te, DAILY_FEATURES, s_tr["label"].to_numpy(),
                   s_ca["label"].to_numpy(), s_te["label"].to_numpy(), m_s.predict(s_te)["score"].to_numpy(),
                   m_s.predict(s_tr)["score"].to_numpy(), s_tr["label"].to_numpy())


def run_london():
    # Londra (probleme injectate), 3 clase
    smp = lcl.build_samples()
    l_tr, l_ca, l_te = (smp[smp.split == x].reset_index(drop=True) for x in ("train", "cal", "test"))
    m_l = train_lcl(smp)
    y_te = l_te["problem"].to_numpy()
    subtle = ~(l_te["kind"].isin(OBVIOUS_KINDS) & (l_te["problem"] == 1)).to_numpy()
    return run_set("Londra (probleme injectate)", l_tr, l_ca, l_te, ALL_FEATURES,
                   l_tr["family"].map(FAMILY_TO_Y).to_numpy(), l_ca["problem"].to_numpy(), y_te,
                   m_l.predict(l_te)["score"].to_numpy(), m_l.predict(l_tr)["score"].to_numpy(),
                   l_tr["problem"].to_numpy(), groups_te=l_te["household"].to_numpy(),
                   value_te=l_te["value_true_lei"].to_numpy(), subsets={"doar_subtile": subtle})


if __name__ == "__main__":
    sys.exit(main())
