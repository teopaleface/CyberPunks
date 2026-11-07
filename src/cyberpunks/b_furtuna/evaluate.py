"""Evaluarea modelului B pe date nevăzute și scrierea raportului `reports/B/metrics.json` (contractul ModelReport).

    uv run python -m cyberpunks.b_furtuna.evaluate            # antrenare 2023-2024, test 2025, state nevăzute
    uv run python -m cyberpunks.b_furtuna.evaluate --no-loso  # fără testul pe state nevăzute (mai rapid)

Ce face:
1. Antrenează pe 2023-2024 (80 de comitate, 8 state SUA) și testează pe 2025 (an nevăzut).
2. Compară cu trei baseline-uri: climatologia pe comitat și lună (folosește istoricul comitatului, pe care
   în România nu-l avem), climatologia pe lună (ce am putea face în România fără model) și regula pe rafală.
3. Generalizare spațială: pe rând, fiecare stat e scos din antrenare și testat pe 2025 (zone fără istoric).
4. Scrie metricile, figurile și modelul (`models/B/b_model.joblib`).
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from zoneinfo import ZoneInfo

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, precision_recall_curve, roc_auc_score

from cyberpunks.b_furtuna import dataset
from cyberpunks.b_furtuna.model import MODEL_ID, QUANTILES, BModel, best_f1_threshold, shap_values, train
from cyberpunks.common.contracts import ModelReport
from cyberpunks.common.paths import REPORTS

OUT_DIR = REPORTS / "B"
TRAIN_YEARS, TEST_YEAR = (2023, 2024), 2025
GUST_RULE_KMH = 70.0
DATASETS = [
    "EAGLE-I, ORNL: Brelsford et al. (2024), Scientific Data 11:271; figshare 10.6084/m9.figshare.24237376.v4 (CC BY 4.0)",
    "Open-Meteo Historical Weather API (archive, best_match: ERA5/ERA5-Land/ECMWF IFS), variabile zilnice, CC BY 4.0",
    "ORNL MCC (clienți modelați pe comitat, 2022), din același set EAGLE-I",
    "US Census Bureau, 2024 Gazetteer (centroizii și suprafața comitatelor)",
]


# ---------------------------------------------------------------------------------------------
# Baseline-uri
# ---------------------------------------------------------------------------------------------


def clim_month(train: pd.DataFrame) -> pd.Series:
    return train.groupby(train["date"].dt.month)["event"].mean()


def predict_clim_month(rates: pd.Series, df: pd.DataFrame) -> np.ndarray:
    return df["date"].dt.month.map(rates).fillna(rates.mean()).to_numpy()


def predict_clim_county_month(train: pd.DataFrame, df: pd.DataFrame, m: float = 20.0) -> np.ndarray:
    """Rata pe comitat și lună, micșorată spre rata lunii (m = câte zile „valorează” rata globală)."""
    month_rate = clim_month(train)
    g = train.groupby(["fips", train["date"].dt.month])["event"].agg(["sum", "size"])
    key = list(zip(df["fips"], df["date"].dt.month, strict=True))
    prior = df["date"].dt.month.map(month_rate).fillna(month_rate.mean()).to_numpy()
    s = np.array([g["sum"].get(k, 0.0) for k in key])
    n = np.array([g["size"].get(k, 0.0) for k in key])
    return (s + m * prior) / (n + m)


GUST_BINS = [0, 30, 40, 50, 60, 70, 80, 90, 1000]


def gust_rule_table(train: pd.DataFrame) -> pd.Series:
    b = pd.cut(train["gust_max"], GUST_BINS, right=False)
    return train.groupby(b, observed=False)["event"].mean()


def predict_gust_rule(table: pd.Series, df: pd.DataFrame) -> np.ndarray:
    b = pd.cut(df["gust_max"], GUST_BINS, right=False)
    return b.map(table).astype(float).fillna(float(table.mean())).to_numpy()


def clim_quantiles(train: pd.DataFrame) -> pd.DataFrame:
    """Cuantilele vârfului (log) în zilele cu eveniment, pe lună: baseline-ul pentru regresia cuantilă."""
    ev = train[train["event"] == 1]
    return ev.groupby(ev["date"].dt.month)["y_log_pct"].quantile(list(QUANTILES)).unstack()


# ---------------------------------------------------------------------------------------------
# Metrici
# ---------------------------------------------------------------------------------------------


def binary_metrics(y: np.ndarray, p: np.ndarray, thr: float, severe: np.ndarray, extreme: np.ndarray) -> dict:
    pred = p >= thr
    tp = int(np.sum(pred & (y == 1)))
    out = {
        "pr_auc": float(average_precision_score(y, p)),
        "roc_auc": float(roc_auc_score(y, p)),
        "brier": float(brier_score_loss(y, p)),
        "log_loss": float(log_loss(y, np.clip(p, 1e-6, 1 - 1e-6))),
        "threshold": float(thr),
        "precision_at_thr": float(tp / max(pred.sum(), 1)),
        "recall_at_thr": float(tp / max(y.sum(), 1)),
        "recall_severe_at_thr": float(np.sum(pred & (severe == 1)) / max(severe.sum(), 1)),
        "recall_extreme_at_thr": float(np.sum(pred & (extreme == 1)) / max(extreme.sum(), 1)),
        "alerts_per_100_zone_days": float(100 * pred.mean()),
    }
    out["f1_at_thr"] = float(2 * out["precision_at_thr"] * out["recall_at_thr"] /
                             max(out["precision_at_thr"] + out["recall_at_thr"], 1e-9))
    return out


def pinball(y: np.ndarray, q_pred: np.ndarray, q: float) -> float:
    d = y - q_pred
    return float(np.mean(np.maximum(q * d, (q - 1) * d)))


def quantile_metrics(y_log: np.ndarray, q_log: np.ndarray, prefix: str = "") -> dict:
    out = {f"{prefix}pinball_q{int(q * 100)}": pinball(y_log, q_log[:, i], q) for i, q in enumerate(QUANTILES)}
    out[f"{prefix}pinball_mean"] = float(np.mean([out[f"{prefix}pinball_q{int(q * 100)}"] for q in QUANTILES]))
    out[f"{prefix}coverage_p10_p90"] = float(np.mean((y_log >= q_log[:, 0]) & (y_log <= q_log[:, 2])))
    return out


def model_quantiles_log(model: BModel, X: pd.DataFrame) -> np.ndarray:
    qs = np.column_stack([model.quantile_models[q].predict(X[model.features]) for q in QUANTILES])
    return np.sort(np.clip(qs, 0, None), axis=1)


# ---------------------------------------------------------------------------------------------
# Rularea
# ---------------------------------------------------------------------------------------------


def evaluate_split(train_df: pd.DataFrame, test_df: pd.DataFrame, with_county_clim: bool = True) -> tuple[dict, BModel]:
    model, _oof = train(train_df)
    tr = train_df[~train_df["wx_missing"]]
    te = test_df[~test_df["wx_missing"]]
    y, sev, ext = te["event"].to_numpy(), te["severe"].to_numpy(), te["extreme"].to_numpy()
    y_tr = tr["event"].to_numpy()
    res: dict = {"prevalence_test": float(y.mean()), "test_rows": len(te), "test_events": int(y.sum())}

    p_model = model.predict_proba(te)
    res["model"] = binary_metrics(y, p_model, model.decision_threshold, sev, ext)

    rates = clim_month(tr)
    p_cm_tr = predict_clim_month(rates, tr)
    res["clim_month"] = binary_metrics(y, predict_clim_month(rates, te), best_f1_threshold(y_tr, p_cm_tr), sev, ext)

    table = gust_rule_table(tr)
    p_g_tr = predict_gust_rule(table, tr)
    res["gust_rule"] = binary_metrics(y, predict_gust_rule(table, te), best_f1_threshold(y_tr, p_g_tr), sev, ext)
    hard = (te["gust_max"] >= GUST_RULE_KMH).to_numpy().astype(float)
    res["gust_rule_70kmh"] = binary_metrics(y, hard, 0.5, sev, ext)

    if with_county_clim:
        p_cc_tr = predict_clim_county_month(tr, tr)
        res["clim_county_month"] = binary_metrics(
            y, predict_clim_county_month(tr, te), best_f1_threshold(y_tr, p_cc_tr), sev, ext
        )

    ev = te["event"] == 1
    if ev.sum() > 0:
        y_log = te.loc[ev, "y_log_pct"].to_numpy()
        res["model"].update(quantile_metrics(y_log, model_quantiles_log(model, te.loc[ev])))
        cq = clim_quantiles(tr)
        months = te.loc[ev, "date"].dt.month
        cq_pred = np.column_stack([months.map(cq[q]).fillna(cq[q].mean()).to_numpy() for q in QUANTILES])
        res["clim_month"].update(quantile_metrics(y_log, cq_pred))
    res["_p_model"] = p_model
    return res, model


def loso(df_train: pd.DataFrame, df_test: pd.DataFrame) -> dict:
    out = {}
    for s in sorted(df_train["state"].unique()):
        tr, te = df_train[df_train["state"] != s], df_test[df_test["state"] == s]
        if te.empty or te["event"].sum() == 0:
            continue
        res, _ = evaluate_split(tr, te, with_county_clim=False)
        res.pop("_p_model", None)
        out[s] = {
            "prevalence": res["prevalence_test"],
            "events": res["test_events"],
            "model_pr_auc": res["model"]["pr_auc"],
            "model_brier": res["model"]["brier"],
            "clim_month_pr_auc": res["clim_month"]["pr_auc"],
            "clim_month_brier": res["clim_month"]["brier"],
            "gust_rule_pr_auc": res["gust_rule"]["pr_auc"],
            "model_recall_severe": res["model"]["recall_severe_at_thr"],
        }
        print(f"  stat nevăzut {s}: PR-AUC model {out[s]['model_pr_auc']:.3f} vs climatologie "
              f"{out[s]['clim_month_pr_auc']:.3f} vs rafală {out[s]['gust_rule_pr_auc']:.3f} (prevalență {out[s]['prevalence']:.3f})")
    return out


def figures(te: pd.DataFrame, p: dict[str, np.ndarray], model: BModel) -> list[str]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    y = te["event"].to_numpy()
    files = []
    # curbele precizie-recall
    fig, ax = plt.subplots(figsize=(6, 4.5))
    names = {"model": "Model LightGBM", "clim_county_month": "Climatologie comitat × lună",
             "clim_month": "Climatologie pe lună", "gust_rule": "Regula pe rafală"}
    for k, label in names.items():
        if k in p:
            prec, rec, _ = precision_recall_curve(y, p[k])
            ax.plot(rec, prec, label=f"{label} (AP {average_precision_score(y, p[k]):.3f})", lw=2 if k == "model" else 1.2)
    ax.axhline(y.mean(), color="grey", ls=":", label=f"Prevalență {y.mean():.3f}")
    ax.set_xlabel("Recall (avarii prinse)")
    ax.set_ylabel("Precizie (alerte corecte)")
    ax.set_title(f"Test pe {TEST_YEAR} (an nevăzut), vârf ≥ 1% din clienți")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig_pr_curves.png", dpi=130)
    plt.close(fig)
    files.append("fig_pr_curves.png")
    # calibrarea
    fig, ax = plt.subplots(figsize=(5, 4.5))
    bins = np.linspace(0, 1, 11)
    for k, label in [("model", "Model (calibrat)"), ("clim_month", "Climatologie pe lună")]:
        idx = np.digitize(p[k], bins) - 1
        xs, ys = [], []
        for b in range(10):
            msk = idx == b
            if msk.sum() >= 20:
                xs.append(p[k][msk].mean())
                ys.append(y[msk].mean())
        ax.plot(xs, ys, "o-", label=label)
    ax.plot([0, 1], [0, 1], "k:", lw=1)
    ax.set_xlabel("Probabilitate prezisă")
    ax.set_ylabel("Frecvență observată")
    ax.set_title(f"Calibrare pe {TEST_YEAR}")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig_reliability.png", dpi=130)
    plt.close(fig)
    files.append("fig_reliability.png")
    # importanța SHAP
    sv = shap_values(model, te)[:, :-1]
    imp = pd.Series(np.abs(sv).mean(axis=0), index=model.features).sort_values()
    fig, ax = plt.subplots(figsize=(6, 5))
    imp.plot.barh(ax=ax, color="#2f6db5")
    ax.set_xlabel("Contribuția medie |SHAP| (log-odds)")
    ax.set_title(f"Ce contează pentru risc (test {TEST_YEAR})")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig_shap_importance.png", dpi=130)
    plt.close(fig)
    files.append("fig_shap_importance.png")
    return files


def run(do_loso: bool = True) -> dict:
    df = pd.read_parquet(dataset.OUT)
    df["date"] = pd.to_datetime(df["date"])
    train_df = df[df["year"].isin(TRAIN_YEARS)]
    test_df = df[df["year"] == TEST_YEAR]
    print(f"antrenare {len(train_df):,} zile-comitat ({int(train_df['event'].sum()):,} evenimente), "
          f"test {len(test_df):,} ({int(test_df['event'].sum()):,})")
    res, model = evaluate_split(train_df, test_df)
    te = test_df[~test_df["wx_missing"]]
    tr = train_df[~train_df["wx_missing"]]
    p = {
        "model": res.pop("_p_model"),
        "clim_county_month": predict_clim_county_month(tr, te),
        "clim_month": predict_clim_month(clim_month(tr), te),
        "gust_rule": predict_gust_rule(gust_rule_table(tr), te),
    }
    files = figures(te, p, model)
    detail = {"main": res, "figures": files, "train_info": model.train_info}
    if do_loso:
        print("generalizare pe state nevăzute (leave-one-state-out):")
        detail["loso"] = loso(train_df, test_df)
        lo = pd.DataFrame(detail["loso"]).T
        detail["loso_summary"] = {
            "model_pr_auc_mean": float(lo["model_pr_auc"].mean()),
            "clim_month_pr_auc_mean": float(lo["clim_month_pr_auc"].mean()),
            "gust_rule_pr_auc_mean": float(lo["gust_rule_pr_auc"].mean()),
            "states_model_beats_clim": int((lo["model_pr_auc"] > lo["clim_month_pr_auc"]).sum()),
            "states": len(lo),
        }
    model.save()

    m, b = res["model"], res["clim_county_month"]
    keys = ["pr_auc", "roc_auc", "brier", "log_loss", "precision_at_thr", "recall_at_thr", "f1_at_thr",
            "recall_severe_at_thr", "recall_extreme_at_thr", "alerts_per_100_zone_days"]
    metrics = {k: round(m[k], 4) for k in keys}
    metrics.update({k: round(v, 4) for k, v in m.items() if k.startswith(("pinball", "coverage"))})
    metrics["prevalence"] = round(res["prevalence_test"], 4)
    metrics["decision_threshold"] = round(model.decision_threshold, 3)
    metrics["pr_auc_gust_rule"] = round(res["gust_rule"]["pr_auc"], 4)
    metrics["pr_auc_clim_month"] = round(res["clim_month"]["pr_auc"], 4)
    if "loso_summary" in detail:
        metrics["loso_pr_auc_mean"] = round(detail["loso_summary"]["model_pr_auc_mean"], 4)
        metrics["loso_clim_month_pr_auc_mean"] = round(detail["loso_summary"]["clim_month_pr_auc_mean"], 4)
    baseline = {k: round(b[k], 4) for k in keys}
    report = ModelReport(
        source="B",
        model_id=MODEL_ID,
        model_version=model.version,
        task="clasificare dezechilibrată calibrată (vârf ≥ 1% din clienți fără curent, zonă × zi) + regresie "
             "cuantilă P10/P50/P90 a vârfului, în zilele cu eveniment",
        dataset=DATASETS,
        split=f"pe timp: antrenare {TRAIN_YEARS[0]}-{TRAIN_YEARS[1]}, test {TEST_YEAR} (an nevăzut), "
              f"{model.train_info['counties']} comitate din 8 state SUA; plus state nevăzute (leave-one-state-out) "
              "în reports/B/metrics_detail.json",
        test_size=res["test_rows"],
        primary_metric="pr_auc",
        metrics=metrics,
        baseline_id="climatologie_comitat_luna (rata istorică pe comitat și lună, 2023-2024)",
        baseline_metrics=baseline,
        synthetic_share=0.0,
        created_at=datetime.now(ZoneInfo("Europe/Bucharest")).replace(microsecond=0),
        reproduce_cmd="uv run python -m cyberpunks.b_furtuna.evaluate",
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "metrics.json").write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    detail_clean = json.loads(json.dumps(detail, default=float))
    (OUT_DIR / "metrics_detail.json").write_text(json.dumps(detail_clean, indent=2, ensure_ascii=False) + "\n",
                                                 encoding="utf-8")
    print(json.dumps({"model": metrics, "baseline_clim_county_month": baseline}, indent=2, ensure_ascii=False))
    return detail


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-loso", action="store_true")
    args = ap.parse_args(argv)
    run(do_loso=not args.no_loso)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
