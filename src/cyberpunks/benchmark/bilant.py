"""Benchmark bilanț pe post: CatBoost față de LightGBM v2, clasificarea celor șase cauze ale lipsei de la post.

Toate etichetele (furt, defecte, pierderi, client la postul greșit) sunt SINTETICE. Pe FeederBW, doar forma
profilelor de consum (importul orar al plecărilor) vine din măsurători reale; rețelele, clienții și diagnosticele
rămân simulate.

Două teste, fiecare cu propriul protocol, refolosit din codul existent:

1. `v2`: testul folosit de v2 (`a_bilant/v2.py`): 300 de posturi din registrul C, rețele nevăzute, 13.200 de
   ferestre de 14 zile. Antrenare pe lotul `trainL` (~3.000 de posturi), validare = 20% din cartierele lui `trainL`
   (`v2.split_by_cluster`). LightGBM: modelul livrat în `models/release/bilant-v2/` (40 de încercări Optuna, obiectiv
   macro-F1 pe argmax). CatBoost: același obiectiv, aceeași validare, 40 de încercări. Bootstrap pe cartiere (31).
2. `feederbw`: lotul cu profile reale FeederBW (`a_bilant/feederbw.py`), split pe plecarea REALĂ (22/8/8).
   LightGBM cu setările v2 și LightGBM optimizat (40 de încercări, obiectiv macro-F1 cu regulile de după model);
   CatBoost, același obiectiv, 40 de încercări. Bootstrap pe cele 8 plecări reale de test.

Regulile de decizie de după clasificare (`v2.full_decision`: abținere, regula perechii, regula contorului martor)
sunt aceleași pentru ambele modele.

    uv run --group bench python -m cyberpunks.benchmark.bilant v2 --trials 40
    uv run --group bench python -m cyberpunks.benchmark.bilant feederbw --trials 40
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass

import numpy as np
import optuna
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.metrics import confusion_matrix, f1_score

from cyberpunks.a_bilant import diagnose as G
from cyberpunks.a_bilant import features as F
from cyberpunks.a_bilant import feederbw as FB
from cyberpunks.a_bilant import normal as N
from cyberpunks.a_bilant import windows as W
from cyberpunks.a_bilant.problems import CLASSES
from cyberpunks.a_bilant.v2 import full_decision, split_by_cluster
from cyberpunks.benchmark import common as C
from cyberpunks.common.paths import DATA_PROCESSED, REPORTS

BASE = DATA_PROCESSED / "bilant"
CACHE = DATA_PROCESSED / "benchmark"
THEFT = "furt_inainte_contor"
LABELS = "SINTETICE: rețele, clienți, pierderi și toate diagnosticele sunt simulate"
CAT_DEFAULT = {"iterations": 800, "learning_rate": 0.08, "depth": 6, "l2_leaf_reg": 3.0, "rsm": 1.0, "subsample": 0.8,
               "class_weight_power": 1.0}


@dataclass
class CatDiagnoser:
    """Aceeași interfață ca `diagnose.Diagnoser` (metoda `proba`), ca regulile de după model să fie identice."""

    model: CatBoostClassifier
    features: list

    def proba(self, X: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame(self.model.predict_proba(X[self.features]), columns=list(CLASSES), index=X.index)


def class_weights(win: pd.DataFrame, power: float) -> tuple[np.ndarray, np.ndarray]:
    """Aceeași schemă ca `diagnose.fit`: clase echilibrate la puterea `power`, înmulțite cu `weight` dacă există."""
    y = win["true_class"].map({c: i for i, c in enumerate(CLASSES)}).to_numpy()
    counts = np.bincount(y, minlength=len(CLASSES)).astype(float)
    w = ((len(y) / (len(CLASSES) * np.maximum(counts, 1))) ** power)[y]
    if "weight" in win.columns:
        w = w * win["weight"].to_numpy()
    return y, w


def fit_cat(win: pd.DataFrame, params: dict, seed: int, threads: int, features: list | None = None) -> CatDiagnoser:
    feats = list(features or W.WIN_FEATURES_V2)
    p = {**CAT_DEFAULT, **params}
    y, w = class_weights(win, p["class_weight_power"])
    m = CatBoostClassifier(
        loss_function="MultiClass", iterations=int(p["iterations"]), learning_rate=float(p["learning_rate"]),
        depth=int(p["depth"]), l2_leaf_reg=float(p["l2_leaf_reg"]), rsm=float(p["rsm"]),
        bootstrap_type="Bernoulli", subsample=float(p["subsample"]), random_seed=seed, thread_count=threads,
        verbose=0, allow_writing_files=False,
    )
    m.fit(win[feats], y, sample_weight=w)
    if list(m.classes_) != list(range(len(CLASSES))):
        raise ValueError("CatBoost nu a văzut toate cele șase clase la antrenare")
    return CatDiagnoser(m, feats)


def cat_space(trial: optuna.Trial) -> dict:
    """Spațiul CatBoost, cu aceleași dimensiuni ca spațiul LightGBM din v2 / feederbw (arbori, pas, complexitate,
    regularizare, eșantionarea coloanelor și a rândurilor, puterea ponderilor de clasă)."""
    return {
        "iterations": trial.suggest_int("iterations", 300, 1500, step=100),
        "learning_rate": trial.suggest_float("learning_rate", 0.02, 0.2, log=True),
        "depth": trial.suggest_int("depth", 4, 9),
        "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 0.1, 30.0, log=True),
        "rsm": trial.suggest_float("rsm", 0.4, 1.0),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0),
        "class_weight_power": trial.suggest_float("class_weight_power", 0.0, 1.0),
    }


def macro(y: np.ndarray, pred: np.ndarray) -> float:
    return float(f1_score(y, pred, labels=list(CLASSES), average="macro", zero_division=0))


def class_f1(y: np.ndarray, pred: np.ndarray, c: str) -> float:
    return float(f1_score(y, pred, labels=[c], average="macro", zero_division=0))


def scores(y: np.ndarray, pred: np.ndarray) -> dict:
    per = f1_score(y, pred, labels=list(CLASSES), average=None, zero_division=0)
    return {"macro_f1": C.r(per.mean()), "accuracy": C.r(np.mean(y == pred)),
            "f1_by_class": {c: C.r(v) for c, v in zip(CLASSES, per, strict=True)},
            "confusion_matrix": {"rows_true_cols_pred": list(CLASSES),
                                 "matrix": confusion_matrix(y, pred, labels=list(CLASSES)).tolist()}}


def paired(y: np.ndarray, base: np.ndarray, cand: np.ndarray, groups: np.ndarray) -> dict:
    """Diferențele candidat - LightGBM, cu interval bootstrap 90% pe grupuri: macro-F1 și F1 pe fiecare clasă."""
    out = {"macro_f1": C.ci90(lambda i: macro(y[i], cand[i]) - macro(y[i], base[i]), groups)}
    for c in CLASSES:
        out[f"f1_{c}"] = C.ci90(lambda i, c=c: class_f1(y[i], cand[i], c) - class_f1(y[i], base[i], c), groups)
    out["classes_worse"] = [c for c in CLASSES if out[f"f1_{c}"]["delta"] < 0]
    out["classes_worse_ci_below_zero"] = [c for c in CLASSES if out[f"f1_{c}"]["ci90"][1] < 0]
    return out


def tune_cat(tr: pd.DataFrame, va: pd.DataFrame, trials: int, seed: int, threads: int, with_rules: bool) -> tuple[dict, list]:
    """Optuna pe validare. `with_rules`: obiectivul trece prin regulile de după model (protocolul FeederBW);
    altfel argmax-ul probabilităților (protocolul v2)."""
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    yv = va["true_class"].to_numpy()
    hist = []

    def objective(trial: optuna.Trial) -> float:
        t0 = time.perf_counter()
        m = fit_cat(tr, cat_space(trial), seed, threads)
        lab = full_decision(m, va)["label"].to_numpy() if with_rules else m.proba(va).idxmax(axis=1).to_numpy()
        v = macro(yv, lab)
        hist.append({"n": trial.number, "val_macro_f1": C.r(v), "seconds": round(time.perf_counter() - t0, 1), **trial.params})
        print(f"CatBoost Optuna {trial.number + 1}/{trials}: F1 validare {v:.4f} ({hist[-1]['seconds']} s)", flush=True)
        return v

    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=seed))
    study.enqueue_trial(CAT_DEFAULT)
    study.optimize(objective, n_trials=trials, show_progress_bar=False)
    return dict(study.best_params), hist


def timed_predict(model, win: pd.DataFrame, times: dict, key: str) -> pd.DataFrame:
    with C.timer(times, key):
        dec = full_decision(model, win)
    return dec


def proba_frame(model, win: pd.DataFrame, prefix: str) -> pd.DataFrame:
    p = model.proba(win)
    return p.rename(columns={c: f"{prefix}_p_{c}" for c in CLASSES}).reset_index(drop=True)


# ------------------------------------------------------------------------------------------------
# 1. testul v2
# ------------------------------------------------------------------------------------------------


def windows_test_release() -> pd.DataFrame:
    """Ferestrele testului v2, construite cu modelele normalului din pachetul livrat (ca în `feederbw.compare_v2`)."""
    path = CACHE / "windows_pop_release_v2.parquet"
    if path.exists():
        return pd.read_parquet(path)
    d = F.load_pool("pop")
    win = W.build_windows(d, W.predict_normal(N.load_for_prediction(), d), "pop")  # un singur proces: vecinii trec de zone
    CACHE.mkdir(parents=True, exist_ok=True)
    win.to_parquet(path)
    return win


def run_v2(trials: int, threads: int) -> dict:
    t_all = time.perf_counter()
    times: dict = {}
    wl = pd.read_parquet(BASE / "windows_trainL.parquet")
    wte = windows_test_release()
    clusters = pd.read_parquet(BASE / "pop" / "posts.parquet").set_index("post_id")["cluster"]
    groups = wte["post_id"].map(clusters).to_numpy()
    y = wte["true_class"].to_numpy()
    cfg = json.loads((REPORTS / "bilant" / "v2_params.json").read_text())
    hist_report = json.loads((REPORTS / "bilant" / "v2_comparison.json").read_text())

    # (a) referința: pachetul livrat, neschimbat
    shipped = G.load_best()
    ref = full_decision(shipped, wte)["label"].to_numpy()
    reference = {"shipped_package": "models/release/bilant-v2 (bilant-diagnoza-lgbm@v2-reconstruit-20261108)",
                 "macro_f1_reproduced": C.r(macro(y, ref)),
                 "macro_f1_report": C.r(hist_report["v2_cautare_optuna"]["macro_f1"]),
                 "test_windows": len(wte), "report_test_windows": hist_report["test_windows"]}
    reference["matches_report"] = abs(reference["macro_f1_reproduced"] - reference["macro_f1_report"]) < 1e-6
    print(f"referință LightGBM v2: F1 {reference['macro_f1_reproduced']} (raport {reference['macro_f1_report']})", flush=True)

    # (b) LightGBM v2 reantrenat din setările salvate, pe aceleași ferestre (verifică reproducerea și dă timpii)
    with C.timer(times, "lightgbm_train_s"):
        lgbm = G.fit(wl, features=cfg["features"], params=cfg["params"], n_jobs=threads)
    dec_l = timed_predict(lgbm, wte, times, "lightgbm_predict_test_s")
    lab_l = dec_l["label"].to_numpy()
    reference["retrained_identical_labels_share"] = C.r(float(np.mean(lab_l == ref)))
    reference["retrained_macro_f1"] = C.r(macro(y, lab_l))

    # (c) CatBoost: aceeași validare (20% din cartierele trainL), același obiectiv, același număr de încercări
    is_val = split_by_cluster(wl)
    with C.timer(times, "catboost_tuning_s"):
        best, hist = tune_cat(wl[~is_val], wl[is_val], trials, seed=0, threads=threads, with_rules=False)
    with C.timer(times, "catboost_train_s"):
        cat = fit_cat(wl, best, seed=0, threads=threads, features=cfg["features"])
    dec_c = timed_predict(cat, wte, times, "catboost_predict_test_s")
    lab_c = dec_c["label"].to_numpy()
    cat_default = fit_cat(wl, CAT_DEFAULT, seed=0, threads=threads, features=cfg["features"])
    lab_cd = full_decision(cat_default, wte)["label"].to_numpy()
    # LightGBM pe aceeași validare, cu setările v2 (pentru comparația pe validare; setările au fost alese pe ea)
    lgbm_val = G.fit(wl[~is_val], features=cfg["features"], params=cfg["params"], n_jobs=threads)
    val_l = macro(wl.loc[is_val, "true_class"].to_numpy(), lgbm_val.proba(wl[is_val]).idxmax(axis=1).to_numpy())

    preds = wte[["post_id", "day", "true_class"]].reset_index(drop=True)
    preds["cluster"] = groups
    preds["lightgbm_shipped_label"] = ref
    preds["lightgbm_label"], preds["catboost_label"], preds["catboost_default_label"] = lab_l, lab_c, lab_cd
    preds["lightgbm_abstain"], preds["catboost_abstain"] = dec_l["abstain"].to_numpy(), dec_c["abstain"].to_numpy()
    preds = pd.concat([preds, proba_frame(lgbm, wte, "lightgbm"), proba_frame(cat, wte, "catboost")], axis=1)
    C.write_predictions("bilant_v2_test", preds)

    out = {
        "problem": "bilanț pe post, diagnosticul celor șase cauze",
        "labels": LABELS,
        "test": "testul v2: 300 de posturi din registrul C (rețele nevăzute), ferestre de 14 zile, model + regula "
                "perechii + regula martorului",
        "train": f"lotul trainL: {wl['post_id'].nunique()} posturi, {len(wl)} ferestre",
        "validation": "20% din cartierele trainL (v2.split_by_cluster, seed 0), pentru alegerea setărilor",
        "bootstrap_unit": f"cartierul postului de test ({len(np.unique(groups))} cartiere), 1000 de reeșantionări, 90%",
        "tuning_budget": {"lightgbm": "40 de încercări Optuna TPE (v2.py, obiectiv macro-F1 argmax pe validare)",
                          "catboost": f"{trials} încercări Optuna TPE, același obiectiv și aceeași validare"},
        "features": cfg["features"], "classes": list(CLASSES),
        "reference_check": reference,
        "lightgbm": {"params": cfg["params"], "validation_macro_f1": C.r(val_l), "test": scores(y, lab_l),
                     "abstain_share": C.r(dec_l["abstain"].mean())},
        "catboost": {"params": best, "validation_macro_f1": C.r(max(h["val_macro_f1"] for h in hist)),
                     "test": scores(y, lab_c), "abstain_share": C.r(dec_c["abstain"].mean()), "trials": hist},
        "catboost_default_untuned": {"params": CAT_DEFAULT, "test": scores(y, lab_cd)},
        "delta_catboost_minus_lightgbm": paired(y, lab_l, lab_c, groups),
        "theft_before_meter": _theft_focus(y, lab_l, lab_c),
        "timing_s": {**times, "threads": threads, "test_windows": len(wte)},
        "environment": C.environment(),
        "seconds_total": round(time.perf_counter() - t_all, 1),
    }
    C.write_json("bilant_v2", out)
    return out


def _theft_focus(y: np.ndarray, lab_l: np.ndarray, lab_c: np.ndarray) -> dict:
    """Furtul înainte de contor: F1, recall, precizie și unde ajung furturile ratate."""
    out = {}
    for name, lab in (("lightgbm", lab_l), ("catboost", lab_c)):
        is_t, pred_t = y == THEFT, lab == THEFT
        tp = int((is_t & pred_t).sum())
        out[name] = {"f1": C.r(class_f1(y, lab, THEFT)), "recall": C.r(tp / max(is_t.sum(), 1)),
                     "precision": C.r(tp / max(pred_t.sum(), 1)), "n_true": int(is_t.sum()),
                     "missed_as": pd.Series(lab[is_t & ~pred_t]).value_counts().to_dict()}
    return out


# ------------------------------------------------------------------------------------------------
# 2. FeederBW, split pe plecarea reală
# ------------------------------------------------------------------------------------------------


def run_feederbw(trials: int, threads: int) -> dict:
    t_all = time.perf_counter()
    times: dict = {}
    if not (FB.OUT / "windows.parquet").exists():
        raise FileNotFoundError("Lipsesc ferestrele FeederBW: rulează `python -m cyberpunks.a_bilant.feederbw prepare` și `tune`")
    manifest = json.loads(FB.MANIFEST.read_text())
    split = manifest["split_feeders"]
    win = pd.read_parquet(FB.OUT / "windows.parquet")
    tr = win[win["source_feeder"].isin(split["train"])]
    va = win[win["source_feeder"].isin(split["validation"])]
    te = win[win["source_feeder"].isin(split["test"])]
    for a, b in ((tr, va), (tr, te), (va, te)):
        assert set(a["source_feeder"]).isdisjoint(b["source_feeder"]) and set(a["post_id"]).isdisjoint(b["post_id"])
    hist_report = json.loads(FB.REPORT.read_text())
    v2_params = json.loads((REPORTS / "bilant" / "v2_params.json").read_text())["params"]
    lgbm_best = hist_report["best_params"]
    y, yv = te["true_class"].to_numpy(), va["true_class"].to_numpy()
    groups = te["source_feeder"].to_numpy()

    # LightGBM, exact ca în feederbw.tune: același seed, aceleași rânduri, aceleași fire (workers=4 în raport)
    with C.timer(times, "lightgbm_v2params_train_s"):
        l_v2 = G.fit(tr, seed=FB.SEED, features=W.WIN_FEATURES_V2, params=v2_params, n_jobs=threads)
    with C.timer(times, "lightgbm_tuned_train_s"):
        l_opt = G.fit(tr, seed=FB.SEED, features=W.WIN_FEATURES_V2, params=lgbm_best, n_jobs=threads)
    dec_l2 = timed_predict(l_v2, te, times, "lightgbm_v2params_predict_test_s")
    dec_lo = timed_predict(l_opt, te, times, "lightgbm_tuned_predict_test_s")
    lab_l2, lab_lo = dec_l2["label"].to_numpy(), dec_lo["label"].to_numpy()
    reference = {"v2params_macro_f1_reproduced": C.r(macro(y, lab_l2)),
                 "v2params_macro_f1_report": C.r(hist_report["test"]["baseline"]["macro_f1"]),
                 "tuned_macro_f1_reproduced": C.r(macro(y, lab_lo)),
                 "tuned_macro_f1_report": C.r(hist_report["test"]["optuna"]["macro_f1"]),
                 "test_windows": len(te), "report_test_windows": hist_report["windows"]["test"]}
    reference["matches_report"] = (abs(reference["v2params_macro_f1_reproduced"] - reference["v2params_macro_f1_report"]) < 1e-6
                                   and abs(reference["tuned_macro_f1_reproduced"] - reference["tuned_macro_f1_report"]) < 1e-6)
    print(f"referință FeederBW: {reference}", flush=True)

    with C.timer(times, "catboost_tuning_s"):
        best, hist = tune_cat(tr, va, trials, seed=FB.SEED, threads=threads, with_rules=True)
    with C.timer(times, "catboost_train_s"):
        cat = fit_cat(tr, best, seed=FB.SEED, threads=threads)
    dec_c = timed_predict(cat, te, times, "catboost_predict_test_s")
    lab_c = dec_c["label"].to_numpy()
    val = {"lightgbm_v2params": C.r(macro(yv, full_decision(l_v2, va)["label"].to_numpy())),
           "lightgbm_tuned": C.r(hist_report["validation"]["optuna_macro_f1"]),
           "catboost_tuned": C.r(max(h["val_macro_f1"] for h in hist))}

    preds = te[["post_id", "source_feeder", "day", "true_class"]].reset_index(drop=True)
    preds["lightgbm_v2params_label"], preds["lightgbm_tuned_label"], preds["catboost_label"] = lab_l2, lab_lo, lab_c
    preds = pd.concat([preds, proba_frame(l_opt, te, "lightgbm_tuned"), proba_frame(cat, te, "catboost")], axis=1)
    C.write_predictions("bilant_feederbw_test", preds)

    out = {
        "problem": "bilanț pe post, diagnosticul celor șase cauze, lot FeederBW",
        "labels": LABELS + "; REAL este doar forma importului orar al plecărilor FeederBW (Netze BW / KIT, CC BY 4.0)",
        "source": manifest["record"], "license": manifest["license"],
        "split_real_feeders": split, "excluded_feeders": manifest["excluded_feeders"],
        "windows": {"train": len(tr), "validation": len(va), "test": len(te)},
        "posts": {"train": int(tr["post_id"].nunique()), "validation": int(va["post_id"].nunique()),
                  "test": int(te["post_id"].nunique())},
        "bootstrap_unit": f"plecarea reală de test ({len(np.unique(groups))} plecări), 1000 de reeșantionări, 90%",
        "tuning_budget": {"lightgbm_tuned": "40 de încercări Optuna TPE (feederbw.tune), obiectiv macro-F1 cu reguli pe validare",
                          "catboost": f"{trials} încercări Optuna TPE, același obiectiv și aceeași validare",
                          "lightgbm_v2params": "fără căutare pe FeederBW (setările v2)"},
        "reference_check": reference,
        "validation_macro_f1": val,
        "lightgbm_v2params": {"params": v2_params, "test": scores(y, lab_l2)},
        "lightgbm_tuned": {"params": lgbm_best, "test": scores(y, lab_lo)},
        "catboost": {"params": best, "test": scores(y, lab_c), "trials": hist},
        "delta_catboost_minus_lightgbm_tuned": paired(y, lab_lo, lab_c, groups),
        "delta_catboost_minus_lightgbm_v2params": paired(y, lab_l2, lab_c, groups),
        "theft_before_meter": {**_theft_focus(y, lab_lo, lab_c),
                               "lightgbm_v2params": _theft_focus(y, lab_l2, lab_c)["lightgbm"]},
        "timing_s": {**times, "threads": threads, "test_windows": len(te)},
        "environment": C.environment(),
        "seconds_total": round(time.perf_counter() - t_all, 1),
    }
    C.write_json("bilant_feederbw", out)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["v2", "feederbw"])
    ap.add_argument("--trials", type=int, default=40)
    ap.add_argument("--threads", type=int, default=None, help="implicit: 8 la v2 (ca v2.py), 4 la FeederBW (ca feederbw.tune)")
    a = ap.parse_args(argv)
    if a.command == "v2":
        run_v2(a.trials, a.threads or 8)
    else:
        run_feederbw(a.trials, a.threads or 4)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
