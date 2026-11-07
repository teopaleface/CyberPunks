"""Evaluarea firului A pe seturi de test separate. Refăce toate cifrele din prezentare.

    uv run python -m cyberpunks.a_contoare.evaluate            # folosește modelele salvate (le antrenează dacă lipsesc)
    uv run python -m cyberpunks.a_contoare.evaluate --retrain  # antrenează din nou, apoi evaluează

Scrie:
- reports/A/metrics.json       contractul ModelReport (modelul agentului față de regula simplă)
- reports/A/metrics_full.json  tot: ambele seturi de test, ambele baseline-uri, intervale bootstrap, pe tipuri,
                               pe niveluri de consum, calibrare, conformal
- reports/A/figures/*.png      curbe precizie-recall, calibrare, precizie pe buget, detecție pe tipuri

Seturile de test:
- SGCC (etichete reale de furt): 20% din clienți, nevăzuți la antrenare și la calibrare;
- Londra (consum real, probleme injectate = etichete sintetice): gospodării nevăzute ȘI perioadă ulterioară
  (sept. 2013 - feb. 2014; antrenarea folosește dec. 2012 - aug. 2013).
K = 1% din contoarele din test (BUDGET_SHARE din metrics.py).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve

from cyberpunks.a_contoare import lcl, sgcc
from cyberpunks.a_contoare import metrics as M
from cyberpunks.a_contoare.baselines import IForestBaseline, rule_score, tune_vee, vee_full_score
from cyberpunks.a_contoare.features import ALL_FEATURES, DAILY_FEATURES
from cyberpunks.a_contoare.inject import BENIGN_KINDS, FAULT_KINDS, KIND_LABEL_RO, TAMPER_KINDS
from cyberpunks.a_contoare.model import MeterModel
from cyberpunks.a_contoare.train import train_lcl, train_sgcc
from cyberpunks.common.contracts import ModelReport
from cyberpunks.common.paths import REPORTS

REPORTS_A = REPORTS / "A"
FIG = REPORTS_A / "figures"
TZ = ZoneInfo("Europe/Bucharest")
N_BOOT = 300
BUDGETS = [0.0025, 0.005, 0.01, 0.02, 0.05, 0.10]
COLORS = {"model": "#1f5fbf", "rule": "#c2410c", "vee": "#d97706", "iforest": "#6b7280"}
NAMES_RO = {
    "model": "LightGBM (al nostru)",
    "rule": "Regula simplă (zero / scădere)",
    "vee": "Regula VEE completă",
    "iforest": "IsolationForest",
}
OBVIOUS_KINDS = ("zero", "stuck", "negative", "gaps")  # le prinde orice verificare VEE


def _r(x: float, nd: int = 4) -> float:
    return float(round(x, nd)) if np.isfinite(x) else float("nan")


def cluster_bootstrap_ci(fn, y, s, groups, n: int = N_BOOT, seed: int = 0) -> tuple[float, float]:
    """Bootstrap pe gospodării (eșantioanele aceleiași gospodării sunt corelate, deci se trag împreună)."""
    rng = np.random.default_rng(seed)
    y, s, groups = np.asarray(y), np.asarray(s), np.asarray(groups)
    uniq, inv = np.unique(groups, return_inverse=True)
    members = [np.flatnonzero(inv == g) for g in range(len(uniq))]
    vals = []
    for _ in range(n):
        pick = rng.integers(0, len(uniq), len(uniq))
        idx = np.concatenate([members[g] for g in pick])
        if y[idx].min() == y[idx].max():
            continue
        vals.append(fn(y[idx], s[idx]))
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return float(lo), float(hi)


def evaluate_set(name: str, y, scores: dict[str, np.ndarray], k: int, groups=None, value_true=None) -> dict:
    """Metrici de clasament pentru model și baseline-uri, cu intervale de încredere și câștigul pe perechi."""
    out: dict = {"n": len(y), "positives": int(np.sum(y)), "prevalence": _r(float(np.mean(y))), "k": int(k)}
    for method, s in scores.items():
        r = M.ranking_metrics(y, s, k, value_true)
        fn_p = lambda yy, ss: M.precision_at_k(yy, ss, max(1, round(len(yy) * k / len(y))))
        if groups is None:
            ci_p = M.bootstrap_ci(fn_p, y, s, N_BOOT)
            ci_ap = M.bootstrap_ci(M.pr_auc, y, s, N_BOOT)
        else:
            ci_p = cluster_bootstrap_ci(fn_p, y, s, groups)
            ci_ap = cluster_bootstrap_ci(M.pr_auc, y, s, groups)
        r["precision_at_k_ci95"] = [_r(ci_p[0]), _r(ci_p[1])]
        r["pr_auc_ci95"] = [_r(ci_ap[0]), _r(ci_ap[1])]
        r["precision_at_budget"] = {f"{b:.4f}": _r(M.precision_at_k(y, s, M.k_for(len(y), b))) for b in BUDGETS}
        out[method] = {kk: (_r(v) if isinstance(v, float) else v) for kk, v in r.items()}
    if "model" in scores:
        for base in (m for m in scores if m != "model"):
            fn = lambda yy, ss: M.precision_at_k(yy, ss, max(1, round(len(yy) * k / len(y))))
            out[f"model_beats_{base}_share"] = _r(M.paired_bootstrap_win(fn, y, scores["model"], scores[base], N_BOOT))
    print(f"[{name}] n={len(y)}, pozitive={int(np.sum(y))}, K={k}")
    for method in scores:
        m = out[method]
        print(
            f"  {method:8s} P@K={m['precision_at_k']:.3f} {m['precision_at_k_ci95']}  PR-AUC={m['pr_auc']:.3f} "
            f"ROC-AUC={m['roc_auc']:.3f}  R@K={m['recall_at_k']:.3f}"
        )
    return out


def false_alarms_by_level(level: np.ndarray, y: np.ndarray, s: np.ndarray, budget: float = 0.05) -> list[dict]:
    """Rata de alarme false pe chintile de consum: ce parte din contoarele FĂRĂ problemă ajung în top `budget`."""
    k = M.k_for(len(y), budget)
    top = np.zeros(len(y), dtype=bool)
    top[M.rank(s)[:k]] = True
    q = pd.qcut(pd.Series(level).rank(method="first"), 5, labels=False).to_numpy()
    rows = []
    for i in range(5):
        m = (q == i) & (y == 0)
        mp = (q == i) & (y == 1)
        rows.append(
            {
                "quintile": i + 1,
                "level_kwh_median": _r(float(np.nanmedian(level[q == i])), 2),
                "false_alarm_rate": _r(float(top[m].mean())) if m.any() else float("nan"),
                "recall": _r(float(top[mp].mean())) if mp.any() else float("nan"),
                "n_normal": int(m.sum()),
                "n_problem": int(mp.sum()),
            }
        )
    return rows


def per_kind(test: pd.DataFrame, s: np.ndarray, budget: float = 0.05) -> list[dict]:
    """Pe fiecare tip injectat: separarea față de contoarele normale (ROC-AUC) și detecția în top `budget`."""
    k = M.k_for(len(test), budget)
    top = np.zeros(len(test), dtype=bool)
    top[M.rank(s)[:k]] = True
    normal = (test["problem"] == 0) & (test["kind"] == "none")
    rows = []
    for kind in (*FAULT_KINDS, *TAMPER_KINDS, *BENIGN_KINDS):
        m = test["kind"].to_numpy() == kind
        if kind in BENIGN_KINDS:
            m &= test["problem"].to_numpy() == 0
        else:
            m &= test["problem"].to_numpy() == 1
        if not m.any():
            continue
        yy = np.r_[np.ones(m.sum()), np.zeros(normal.sum())]
        ss = np.r_[s[m], s[normal.to_numpy()]]
        rows.append(
            {
                "kind": kind,
                "label_ro": KIND_LABEL_RO.get(kind, kind),
                "family": "benign" if kind in BENIGN_KINDS else ("faulty" if kind in FAULT_KINDS else "tamper"),
                "n": int(m.sum()),
                "roc_auc_vs_normal": _r(M.roc_auc(yy, ss)),
                "flagged_share_at_5pct": _r(float(top[m].mean())),
            }
        )
    return rows


def type_accuracy(test: pd.DataFrame, pred: pd.DataFrame) -> dict:
    """Dintre problemele reale din test, la câte modelul ghicește familia (defect sau manipulare)."""
    m = test["problem"].to_numpy() == 1
    ok = pred["label"].to_numpy()[m] == test["family"].to_numpy()[m]
    return {"family_accuracy_on_problems": _r(float(ok.mean())), "n": int(m.sum())}


# --------------------------------------------------------------------------------------------
# Figuri
# --------------------------------------------------------------------------------------------


def fig_pr(panels: list[tuple[str, np.ndarray, dict[str, np.ndarray]]]) -> None:
    fig, axes = plt.subplots(1, len(panels), figsize=(6 * len(panels), 4.6))
    for ax, (title, y, scores) in zip(np.atleast_1d(axes), panels, strict=True):
        for method, s in scores.items():
            p, r, _ = precision_recall_curve(y, np.nan_to_num(s, nan=-1e9))
            ax.plot(r, p, color=COLORS[method], lw=2, label=f"{NAMES_RO[method]} (PR-AUC {M.pr_auc(y, s):.2f})")
        ax.axhline(np.mean(y), color="#9ca3af", ls=":", lw=1, label=f"la întâmplare ({np.mean(y):.3f})")
        ax.set(xlabel="Recall (ce parte din probleme găsim)", ylabel="Precizie (câte vizite sunt utile)", title=title)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1.02)
        ax.legend(fontsize=8, loc="upper right")
        ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG / "pr_curves.png", dpi=140, bbox_inches="tight")
    plt.close(fig)


def fig_budget(panels: list[tuple[str, np.ndarray, dict[str, np.ndarray]]]) -> None:
    budgets = np.array([0.0025, 0.005, 0.0075, 0.01, 0.015, 0.02, 0.03, 0.05, 0.075, 0.10])
    fig, axes = plt.subplots(1, len(panels), figsize=(6 * len(panels), 4.4))
    for ax, (title, y, scores) in zip(np.atleast_1d(axes), panels, strict=True):
        for method, s in scores.items():
            prec = [M.precision_at_k(y, s, M.k_for(len(y), b)) for b in budgets]
            ax.plot(budgets * 100, prec, marker="o", color=COLORS[method], lw=2, label=NAMES_RO[method])
        ax.axvline(1.0, color="#111827", ls="--", lw=1)
        ax.text(1.05, 0.03, "K = 1%\n(o săptămână de vizite)", fontsize=8)
        ax.set(xlabel="Contoare vizitate (% din total)", ylabel="Precizia@K", title=title)
        ax.set_ylim(0, 1.02)
        ax.legend(fontsize=8)
        ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG / "precision_at_budget.png", dpi=140, bbox_inches="tight")
    plt.close(fig)


def fig_calibration(panels: list[tuple[str, np.ndarray, np.ndarray]]) -> None:
    fig, axes = plt.subplots(1, len(panels), figsize=(5 * len(panels), 4.6))
    for ax, (title, y, p) in zip(np.atleast_1d(axes), panels, strict=True):
        rows = M.reliability_table(y, p, 10)
        ax.plot([0, 1], [0, 1], color="#9ca3af", ls=":", lw=1)
        ax.plot([r["p_mean"] for r in rows], [r["freq"] for r in rows], marker="o", color=COLORS["model"], lw=2)
        ax.set(
            xlabel="Scorul calibrat (probabilitatea spusă de model)",
            ylabel="Frecvența reală a problemelor",
            title=f"{title}\nBrier {M.brier(y, p):.3f}, ECE {M.ece(y, p):.3f}",
        )
        hi = max(0.05, max(max(r["p_mean"], r["freq"]) for r in rows) * 1.1)
        ax.set_xlim(0, hi)
        ax.set_ylim(0, hi)
        ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG / "calibration.png", dpi=140, bbox_inches="tight")
    plt.close(fig)


def fig_kinds(rows: list[dict]) -> None:
    rows = sorted(rows, key=lambda r: (r["family"], -r["roc_auc_vs_normal"]))
    fig, ax = plt.subplots(figsize=(8, 0.34 * len(rows) + 1.2))
    colors = {"faulty": "#1f5fbf", "tamper": "#b91c1c", "benign": "#6b7280"}
    labels = [f"{r['label_ro']} (n={r['n']})" for r in rows]
    ax.barh(labels, [r["flagged_share_at_5pct"] for r in rows], color=[colors[r["family"]] for r in rows])
    ax.invert_yaxis()
    ax.set_xlabel("Ce parte ajunge în primele 5% din clasament\n(gri: schimbări normale, deci alarme false)")
    ax.set_xlim(0, 1)
    ax.set_title("Detecția pe tipuri, Londra (test)\nalbastru: defect, roșu: manipulare")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG / "detection_by_kind.png", dpi=140, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------------------------


def run(retrain: bool = False) -> dict:
    np.seterr(all="ignore")
    REPORTS_A.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)

    # SGCC: etichete reale
    f = sgcc.build_features()
    s_tr, s_ca, s_te = (f[f.split == x].reset_index(drop=True) for x in ("train", "cal", "test"))
    vee_s = tune_vee(s_ca, s_ca["label"].to_numpy(), M.k_for(len(s_ca)), window_wide=True)
    m_sgcc = train_sgcc(f) if retrain else _load_or_train("a-lgbm-sgcc", lambda: train_sgcc(f))
    y_s = s_te["label"].to_numpy()
    sc_s = {
        "model": m_sgcc.predict(s_te)["score"].to_numpy(),
        "rule": rule_score(s_te, zero_col="longest_zero_run", drop_col="max_drop"),
        "vee": vee_full_score(s_te, window_wide=True, **vee_s),
        "iforest": IForestBaseline(DAILY_FEATURES).fit(s_tr).score(s_te),
    }
    k_s = M.k_for(len(y_s))
    res_s = evaluate_set("SGCC, etichete reale", y_s, sc_s, k_s)
    res_s["calibration"] = {"brier": _r(M.brier(y_s, sc_s["model"])), "ece": _r(M.ece(y_s, sc_s["model"]))}
    res_s["conformal"] = {kk: _r(v) for kk, v in m_sgcc.conformal.coverage(sc_s["model"], y_s).items()}
    res_s["false_alarms_by_level"] = false_alarms_by_level(s_te["level_kwh"].to_numpy(), y_s, sc_s["model"])

    # Londra: probleme injectate (etichete sintetice), gospodării nevăzute și perioadă ulterioară
    smp = lcl.build_samples()
    l_tr, l_ca, l_te = (smp[smp.split == x].reset_index(drop=True) for x in ("train", "cal", "test"))
    vee_l = tune_vee(l_ca, l_ca["problem"].to_numpy(), M.k_for(len(l_ca)))
    m_lcl = train_lcl(smp) if retrain else _load_or_train("a-lgbm", lambda: train_lcl(smp))
    pred = m_lcl.predict(l_te)
    y_l = l_te["problem"].to_numpy()
    sc_l = {
        "model": pred["score"].to_numpy(),
        "rule": rule_score(l_te),
        "vee": vee_full_score(l_te, **vee_l),
        "iforest": IForestBaseline(ALL_FEATURES).fit(l_tr).score(l_te),
    }
    k_l = M.k_for(len(y_l))
    res_l = evaluate_set(
        "Londra, probleme injectate", y_l, sc_l, k_l, groups=l_te["household"].to_numpy(),
        value_true=l_te["value_true_lei"].to_numpy(),
    )
    res_l["calibration"] = {"brier": _r(M.brier(y_l, sc_l["model"])), "ece": _r(M.ece(y_l, sc_l["model"])),
                            "reliability": M.reliability_table(y_l, sc_l["model"])}
    res_l["conformal"] = {kk: _r(v) for kk, v in m_lcl.conformal.coverage(sc_l["model"], y_l).items()}
    # problemele subtile: fără cele evidente pe care le prinde orice verificare VEE (zero, blocat, negative, goluri)
    subtle = ~(l_te["kind"].isin(OBVIOUS_KINDS) & (l_te["problem"] == 1)).to_numpy()
    res_l["subtle_only"] = evaluate_set(
        "Londra, doar problemele subtile", y_l[subtle], {m_: v[subtle] for m_, v in sc_l.items()},
        M.k_for(int(subtle.sum())), groups=l_te["household"].to_numpy()[subtle],
        value_true=l_te["value_true_lei"].to_numpy()[subtle],
    )
    res_l["per_kind_model"] = per_kind(l_te, sc_l["model"])
    res_l["per_kind_vee"] = per_kind(l_te, sc_l["vee"])
    res_l["per_kind_rule"] = per_kind(l_te, sc_l["rule"])
    res_l["type_accuracy"] = type_accuracy(l_te, pred)
    res_l["false_alarms_by_level"] = false_alarms_by_level(l_te["level_kwh"].to_numpy(), y_l, sc_l["model"])
    res_l["false_alarms_by_level_rule"] = false_alarms_by_level(l_te["level_kwh"].to_numpy(), y_l, sc_l["rule"])

    fig_pr([("SGCC: furt, etichete reale (test)", y_s, sc_s), ("Londra: probleme injectate (test)", y_l, sc_l)])
    fig_budget([("SGCC: furt, etichete reale", y_s, sc_s), ("Londra: probleme injectate", y_l, sc_l)])
    fig_calibration([("SGCC (test)", y_s, sc_s["model"]), ("Londra (test)", y_l, sc_l["model"])])
    fig_kinds(res_l["per_kind_model"])

    now = datetime.now(TZ).replace(microsecond=0)
    full = {
        "created_at": now.isoformat(),
        "budget_share": M.BUDGET_SHARE,
        "vee_thresholds_from_calibration": {"sgcc": vee_s, "lcl": vee_l},
        "models": {"a-lgbm": m_lcl.version, "a-lgbm-sgcc": m_sgcc.version},
        "sgcc_real_labels": res_s,
        "lcl_injected": res_l,
        "notes": [
            "Londra: etichete SINTETICE (probleme injectate de noi peste consum real), prevalență 3% defecte + 2% furt.",
            "Intervalele de încredere: bootstrap pe clienți (SGCC) și pe gospodării (Londra), 95%.",
        ],
    }
    (REPORTS_A / "metrics_full.json").write_text(json.dumps(full, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    keys = ["precision_at_k", "recall_at_k", "pr_auc", "roc_auc"]
    metrics = {kk: res_l["model"][kk] for kk in keys}
    metrics.update({"value_at_k_lei": res_l["model"]["value_at_k_lei"], "brier": res_l["calibration"]["brier"],
                    "ece": res_l["calibration"]["ece"]})
    metrics.update({f"sgcc_{kk}": res_s["model"][kk] for kk in keys})
    metrics.update({f"iforest_{kk}": res_l["iforest"][kk] for kk in keys})
    metrics.update({f"vee_{kk}": res_l["vee"][kk] for kk in keys})
    metrics.update({f"subtle_{kk}": res_l["subtle_only"]["model"][kk] for kk in keys})
    metrics.update({f"subtle_vee_{kk}": res_l["subtle_only"]["vee"][kk] for kk in keys})
    metrics.update({f"sgcc_vee_{kk}": res_s["vee"][kk] for kk in keys})
    metrics.update({f"sgcc_iforest_{kk}": res_s["iforest"][kk] for kk in keys})
    baseline = {kk: res_l["rule"][kk] for kk in keys}
    baseline["value_at_k_lei"] = res_l["rule"]["value_at_k_lei"]
    baseline.update({f"subtle_{kk}": res_l["subtle_only"]["rule"][kk] for kk in keys})
    baseline.update({f"sgcc_{kk}": res_s["rule"][kk] for kk in keys})
    report = ModelReport(
        source="A",
        model_id="a-lgbm",
        model_version=m_lcl.version,
        task="clasificare dezechilibrată: contor normal / defect / manipulat (scor calibrat de problemă, clasament sub capacitate)",
        dataset=[
            (
                "Low Carbon London, UK Power Networks, consum real la 30 min, CC BY 4.0 (London Datastore); "
                "defecte și furturi injectate de noi (SINTETIC)"
            ),
            (
                "SGCC, State Grid Corporation of China, consum zilnic cu etichete reale de furt (Zheng et al. 2018, "
                "IEEE TII, DOI 10.1109/TII.2017.2785963); metricile sgcc_* sunt ale modelului a-lgbm-sgcc"
            ),
        ],
        split=(
            "Londra: gospodării nevăzute și perioadă ulterioară (test sept. 2013 - feb. 2014, antrenare dec. 2012 - "
            "aug. 2013); SGCC: 20% din clienți, stratificat, nevăzuți. K = 1% din contoare."
        ),
        test_size=int(len(y_l) + len(y_s)),
        primary_metric="precision_at_k",
        metrics=metrics,
        baseline_id="regula-vee (zero >= 7 zile sau scădere >= 50% față de propriul istoric)",
        baseline_metrics=baseline,
        synthetic_share=_r(len(y_l) / (len(y_l) + len(y_s))),
        created_at=now,
        reproduce_cmd="uv run python -m cyberpunks.a_contoare.evaluate --retrain",
    )
    (REPORTS_A / "metrics.json").write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(f"scris: {REPORTS_A / 'metrics.json'}, {REPORTS_A / 'metrics_full.json'}, figuri în {FIG}")
    return full


def _load_or_train(model_id: str, trainer) -> MeterModel:
    try:
        return MeterModel.load(model_id)
    except FileNotFoundError:
        return trainer()


def main() -> int:
    run(retrain="--retrain" in sys.argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
