"""Evaluarea bilanțului pe post: scrie `reports/bilant/metrics.json` (contractul ModelReport) și figurile.

    uv run python -m cyberpunks.a_bilant.dataset      # o dată: lotul simulat (~1 minut, 4 procese)
    uv run python -m cyberpunks.a_bilant.evaluate

Testul: zilele curate ale celor 300 de posturi din registrul C (rețele nevăzute la antrenare). Totul e SIMULARE pe
date publice, gândită pentru datele PPC.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from cyberpunks.a_bilant import features as F
from cyberpunks.a_bilant import normal as N
from cyberpunks.common.contracts import ModelReport
from cyberpunks.common.paths import REPORTS

OUT = REPORTS / "bilant"
DATASET = [
    "SimBench 1-LV-* (rețele de joasă tensiune și profile de consum, ODbL), variante SINTETICE construite de firul C",
    "Open-Meteo archive (CC BY 4.0), București-Ilfov, orar, 2024-07-01 - 2025-07-08",
    "Registrul de posturi al firului C (poziții OpenStreetMap, ODbL; rețelele din spate sintetice)",
    "Probleme ascunse de noi (contoare, furt înainte de contor, pierderi tehnice, client la postul greșit, contor de post setat greșit): SINTETIC",
]


def git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:  # noqa: BLE001
        return "nogit"


def eval_normal(tr: pd.DataFrame, te: pd.DataFrame) -> tuple[dict, dict, dict[str, N.NormalModel], pd.DataFrame]:
    trc = tr[tr["clean"] & (tr["hist_days"] > 0)]
    tec = te[te["clean"] & (te["hist_days"] > 0)].copy()
    y = tec["short_kwh"].to_numpy()
    models = N.fit_pair(trc)
    model = models["warm"]
    pred = model.predict(tec)
    m = N.interval_metrics(y, pred)
    base_fix = N.interval_metrics(y, N.FixedPercent.fit(trc).predict(tec))
    base_phys = N.interval_metrics(y, N.PhysicsI2R.fit(trc).predict(tec))
    # fără istoricul postului (post nou, fără zile curate): aceleași trăsături, istoricul golit
    m_cold = N.interval_metrics(y, models["cold"].predict(N.drop_history(tec)))
    tec[["p10", "p50", "p90"]] = pred.to_numpy()
    metrics = {f"normal_{k}": v for k, v in m.items()}
    metrics.update({f"normal_fara_istoric_{k}": v for k, v in m_cold.items() if k in ("mae_kwh_day", "coverage_p10_p90")})
    metrics.update({f"procent_fix_{k}": v for k, v in base_fix.items() if k in ("mae_kwh_day", "coverage_p10_p90", "interval_width_kwh_day")})
    metrics["normal_test_days"] = float(len(tec))
    metrics["normal_test_posts"] = float(tec["post_id"].nunique())
    metrics["normal_mean_loss_kwh_day"] = float(np.mean(y))
    metrics["normal_median_loss_pct_throughput"] = float(np.median(y / tec["abs_kwh"].clip(lower=1e-3)) * 100)
    baseline = {f"normal_{k}": v for k, v in base_phys.items()}
    return metrics, baseline, models, tec


def fig_normal(tec: pd.DataFrame) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    OUT.mkdir(parents=True, exist_ok=True)
    s = tec.sample(min(4000, len(tec)), random_state=0)
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.5))
    ax[0].scatter(s["p50"], s["short_kwh"], s=3, alpha=0.3, color="#2b6cb0")
    lim = float(np.quantile(s["short_kwh"], 0.995))
    ax[0].plot([0, lim], [0, lim], color="#444", lw=1)
    ax[0].set_xlim(0, lim)
    ax[0].set_ylim(0, lim)
    ax[0].set_xlabel("pierderea normală estimată P50 (kWh/zi)")
    ax[0].set_ylabel("lipsa reală la post (kWh/zi)")
    ax[0].set_title("Rețele nevăzute, zile fără probleme")
    pid = tec.groupby("post_id")["short_kwh"].mean().sort_values().index[len(tec["post_id"].unique()) // 2]
    g = tec[tec["post_id"] == pid].sort_values("day")
    ax[1].fill_between(g["date"], g["p10"], g["p90"], color="#90cdf4", alpha=0.6, label="interval P10-P90")
    ax[1].plot(g["date"], g["p50"], color="#2b6cb0", lw=1, label="normal P50")
    ax[1].plot(g["date"], g["short_kwh"], color="#c53030", lw=0.8, label="lipsa reală")
    ax[1].set_title(f"{pid}: pierderea normală pe zi")
    ax[1].set_ylabel("kWh/zi")
    ax[1].legend(fontsize=8)
    fig.suptitle("Bilanț pe post, modelul pierderii normale (SIMULARE pe date publice)", fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "normal_loss.png", dpi=130)
    plt.close(fig)


def main() -> None:
    tr = F.load_pool("train")
    te = F.load_pool("pop")
    metrics, baseline, models, tec = eval_normal(tr, te)
    models["warm"].save("normal")
    models["cold"].save("normal_cold")
    fig_normal(tec)
    sha = git_sha()
    report = ModelReport(
        source="A",
        model_id="bilant-normal-lgbm",
        model_version=f"bilant-normal-lgbm@{sha}",
        task="regresie cuantilă (P10/P50/P90): pierderea normală pe post și zi, kWh",
        dataset=DATASET,
        split="antrenare: 300 de posturi sintetice noi (lotul train); test: cele 300 de posturi din registrul C (rețele nevăzute), zilele fără probleme ascunse, cu cel puțin 21 de zile de istoric",
        test_size=int(metrics["normal_test_days"]),
        primary_metric="normal_mae_kwh_day",
        metrics={k: round(float(v), 4) for k, v in metrics.items()},
        baseline_id="fizic-i2r (a·ΣP²·R/U² + b·nr. contoare, cele mai mici pătrate); al doilea reper: procent-fix",
        baseline_metrics={k: round(float(v), 4) for k, v in baseline.items()},
        synthetic_share=1.0,
        created_at=datetime.now(ZoneInfo("Europe/Bucharest")).replace(microsecond=0),
        reproduce_cmd="uv run python -m cyberpunks.a_bilant.dataset && uv run python -m cyberpunks.a_bilant.evaluate",
    )
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "metrics.json").write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: round(v, 3) for k, v in report.metrics.items()}, indent=1, ensure_ascii=False))
    print("baseline", json.dumps({k: round(v, 3) for k, v in report.baseline_metrics.items()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
