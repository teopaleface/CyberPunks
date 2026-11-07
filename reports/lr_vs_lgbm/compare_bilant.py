"""Regresie logistică (multinomială) vs LightGBM pentru diagnosticul cauzei din bilanțul pe post.
# Rulare (din rădăcina repo-ului, pe main): uv run python reports/lr_vs_lgbm/compare_a.py [sgcc|london|all]
# Cere datele A (make a-data) sau, pentru bilanț, ferestrele din make bilant-data bilant-eval.

Folosește ferestrele salvate de `cyberpunks.a_bilant.evaluate` (antrenare: lotul train; test: lotul pop, rețele
nevăzute). Aceleași features (WIN_FEATURES), aceleași ponderi pe clase, aceeași regulă de abținere (decide +
pair_consistency). C se alege prin validare încrucișată grupată pe posturi, doar pe lotul de antrenare.
Verdict: macro F1 pe test (metrica echipei), cu bootstrap pereche pe posturi.
"""

from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import QuantileTransformer, StandardScaler

from cyberpunks.a_bilant import diagnose as G
from cyberpunks.a_bilant.problems import CLASSES
from cyberpunks.a_bilant.windows import WIN_FEATURES
from cyberpunks.common.paths import DATA_PROCESSED

C_GRID = [0.01, 0.1, 1.0, 10.0]
N_BOOT = 1000


def weights(y):
    counts = np.bincount(y, minlength=len(CLASSES)).astype(float)
    return (len(y) / (len(CLASSES) * np.maximum(counts, 1)))[y]


def pipe(kind, c):
    pre = StandardScaler() if kind == "std" else QuantileTransformer(output_distribution="normal", n_quantiles=1000,
                                                                     random_state=0)
    return make_pipeline(SimpleImputer(strategy="median", add_indicator=True), pre,
                         LogisticRegression(C=c, max_iter=5000))


def X(w):
    return w[WIN_FEATURES].replace([np.inf, -np.inf], np.nan).astype(float)


def fit_lr(kind, wtr, y):
    xs, g, sw = X(wtr), wtr["post_id"].to_numpy(), weights(y)
    best = None
    for c in C_GRID:
        f1s = []
        for a, b in GroupKFold(n_splits=4).split(xs, y, g):
            p = pipe(kind, c).fit(xs.iloc[a], y[a], logisticregression__sample_weight=sw[a])
            f1s.append(f1_score(y[b], p.predict(xs.iloc[b]), average="macro"))
        print(f"    LR-{kind} C={c:<5} macro F1 (CV pe antrenare) = {np.mean(f1s):.4f}", flush=True)
        if best is None or np.mean(f1s) > best[0]:
            best = (np.mean(f1s), c)
    return pipe(kind, best[1]).fit(xs, y, logisticregression__sample_weight=sw), best[1]


def evaluate(proba: pd.DataFrame, wte: pd.DataFrame) -> tuple[dict, np.ndarray, np.ndarray]:
    y = wte["true_class"].to_numpy()
    dec = G.pair_consistency(wte, G.decide(proba, wte))
    lab = dec["label"].to_numpy()
    raw = np.array(CLASSES)[proba.to_numpy().argmax(axis=1)]
    m = {"macro_f1": f1_score(y, lab, average="macro"), "accuracy": accuracy_score(y, lab),
         "abstain_rate": float(dec["abstain"].mean()),
         "macro_f1_fara_abtineri": f1_score(y[~dec["abstain"]], lab[~dec["abstain"]], average="macro"),
         "macro_f1_argmax_brut": f1_score(y, raw, average="macro")}
    for c, f in zip(CLASSES, f1_score(y, lab, average=None, labels=list(CLASSES)), strict=True):
        m[f"f1_{c}"] = float(f)
    return {k: float(v) for k, v in m.items()}, lab, y


def paired_boot(y, lab_a, lab_b, groups, n=N_BOOT, seed=0):
    rng = np.random.default_rng(seed)
    uniq, inv = np.unique(groups, return_inverse=True)
    members = [np.flatnonzero(inv == g) for g in range(len(uniq))]
    d = []
    for _ in range(n):
        idx = np.concatenate([members[g] for g in rng.integers(0, len(uniq), len(uniq))])
        d.append(f1_score(y[idx], lab_a[idx], average="macro", labels=list(CLASSES), zero_division=0)
                 - f1_score(y[idx], lab_b[idx], average="macro", labels=list(CLASSES), zero_division=0))
    d = np.asarray(d)
    return {"mean_diff": float(d.mean()), "ci95": [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))],
            "p_lr_better": float((d > 0).mean())}


def main() -> int:
    np.seterr(all="ignore")
    wtr = pd.read_parquet(DATA_PROCESSED / "bilant" / "windows_train.parquet")
    wpop = pd.read_parquet(DATA_PROCESSED / "bilant" / "windows_pop.parquet")
    wte = wpop[[c for c in wtr.columns if c in wpop.columns]]
    y_tr = wtr["true_class"].map({c: i for i, c in enumerate(CLASSES)}).to_numpy()
    print(f"ferestre: antrenare {len(wtr)}, test {len(wte)}")
    print("clase test:", wte["true_class"].value_counts().to_dict())

    out = {"n_train": len(wtr), "n_test": len(wte), "models": {}, "train_macro_f1": {}, "paired_bootstrap_lr_minus_lgbm": {}}
    lgbm = G.fit(wtr)
    m_lgbm, lab_lgbm, y = evaluate(lgbm.proba(wte), wte)
    out["models"]["lgbm"] = m_lgbm
    out["train_macro_f1"]["lgbm"] = float(f1_score(wtr["true_class"], np.array(CLASSES)[lgbm.proba(wtr).to_numpy().argmax(1)], average="macro"))
    rl = G.rules(wte).to_numpy()
    out["models"]["reguli"] = {"macro_f1": float(f1_score(y, rl, average="macro")), "accuracy": float(accuracy_score(y, rl))}
    groups = wte["post_id"].to_numpy()
    for kind in ("std", "quantile"):
        p, c = fit_lr(kind, wtr, y_tr)
        proba = pd.DataFrame(p.predict_proba(X(wte)), columns=list(CLASSES), index=wte.index)
        m, lab, _ = evaluate(proba, wte)
        m["C"] = c
        out["models"][f"lr_{kind}"] = m
        out["train_macro_f1"][f"lr_{kind}"] = float(f1_score(y_tr, p.predict(X(wtr)), average="macro"))
        out["paired_bootstrap_lr_minus_lgbm"][f"lr_{kind}"] = paired_boot(y, lab, lab_lgbm, groups)
    for k, v in out["models"].items():
        print(f"  {k:12s} macro F1={v['macro_f1']:.3f}  acuratețe={v['accuracy']:.3f}"
              + (f"  abțineri={v['abstain_rate']:.3f}" if "abstain_rate" in v else ""))
    print(json.dumps(out["paired_bootstrap_lr_minus_lgbm"], indent=1))
    with open("reports/lr_vs_lgbm/results_bilant.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    print("scris: reports/lr_vs_lgbm/results_bilant.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
