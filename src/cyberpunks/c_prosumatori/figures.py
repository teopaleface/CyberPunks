"""Figurile din reports/C/figures, din predicțiile de test (rețele nevăzute, luni nevăzute).

    uv run python -m cyberpunks.c_prosumatori.figures
"""

from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cyberpunks.common.paths import DATA_PROCESSED, OUTPUTS, REPORTS

FIG = REPORTS / "C" / "figures"
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"  # paleta categorială (ordinea fixă), validată în abilitatea dataviz
LIMIT = 1.10

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "text.color": INK, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "font.size": 10, "axes.titlesize": 11,
    "axes.titleweight": "bold", "legend.frameon": False, "lines.linewidth": 1.6,
})


def _save(fig, name: str) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / name, dpi=160, bbox_inches="tight")
    plt.close(fig)


def pred_vs_sim(res: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.6), sharex=True, sharey=True)
    lo, hi = 0.94, 1.20
    for ax, col, title in ((axes[0], "m_q50", "Modelul (LightGBM)"), (axes[1], "b_q50", "Baseline (soare × kW/kVA)")):
        ax.hexbin(res["vmax_day"], res[col].clip(lo, hi), gridsize=70, extent=(lo, hi, lo, hi), bins="log", cmap="Blues", mincnt=1, linewidths=0)
        ax.plot([lo, hi], [lo, hi], color=INK2, lw=1, ls="--")
        ax.axvline(LIMIT, color=INK2, lw=0.8, ls=":")
        ax.axhline(LIMIT, color=INK2, lw=0.8, ls=":")
        mae = float(np.mean(np.abs(res["vmax_day"] - res[col])))
        ax.set_title(f"{title}: MAE {mae:.4f} pu".replace(".", ","), loc="left")
        ax.set_xlabel("tensiunea maximă din simulare (pu)")
        ax.text(LIMIT + 0.003, lo + 0.005, "1,10 pu", color=INK2, fontsize=8)
    axes[0].set_ylabel("tensiunea maximă prezisă, P50 (pu)")
    fig.suptitle("Rețele nevăzute, zile din 2025-2026: fiecare punct e o zi a unui post", x=0.01, ha="left", fontsize=10, color=INK2)
    _save(fig, "pred_vs_sim.png")


def mae_by_topology(detail: dict) -> None:
    topo = list(detail["by_topology"])
    m = [detail["by_topology"][t]["model"]["mae_vmax_pu"] for t in topo]
    b = [detail["by_topology"][t]["baseline"]["mae_vmax_pu"] for t in topo]
    x = np.arange(len(topo))
    fig, ax = plt.subplots(figsize=(8, 3.8))
    ax.bar(x - 0.2, m, width=0.38, color=S1, label="model", edgecolor=SURFACE, linewidth=2)
    ax.bar(x + 0.2, b, width=0.38, color=S2, label="baseline", edgecolor=SURFACE, linewidth=2)
    ax.set_xticks(x, topo)
    ax.set_ylabel("MAE tensiune maximă (pu)")
    ax.set_title("Eroarea pe fiecare topologie lăsată deoparte la antrenare", loc="left")
    ax.legend(loc="upper left", ncols=2)
    ax.grid(axis="x", visible=False)
    _save(fig, "mae_by_topology.png")


def reliability(res: pd.DataFrame) -> None:
    bins = np.linspace(0, 1, 11)
    fig, ax = plt.subplots(figsize=(5.2, 4.6))
    ax.plot([0, 1], [0, 1], color=INK2, lw=1, ls="--")
    for col, color, name in (("m_p_exceed", S1, "model calibrat"), ("r_p_exceed", S3, "model necalibrat"), ("b_p_exceed", S2, "baseline")):
        p = res[col].to_numpy()
        idx = np.clip(np.digitize(p, bins) - 1, 0, 9)
        xs, ys = [], []
        for k in range(10):
            sel = idx == k
            if sel.sum() >= 50:
                xs.append(p[sel].mean())
                ys.append(res["exceed"].to_numpy()[sel].mean())
        ax.plot(xs, ys, color=color, marker="o", ms=4, label=name)
    ax.set_xlabel("probabilitatea prezisă de depășire")
    ax.set_ylabel("frecvența reală în simulare")
    ax.set_title("Calibrarea P(tensiune > 1,10 pu)", loc="left")
    ax.legend(loc="upper left")
    _save(fig, "reliability.png")


def example_series(scenario: str = "demo-vara") -> None:
    wi = OUTPUTS / "work_items" / scenario / "C.jsonl"
    if not wi.exists():
        return
    items = [json.loads(x) for x in wi.read_text().splitlines() if x.strip()]
    if not items:
        return
    it = items[0]
    s = json.loads((OUTPUTS / "series" / scenario / f"{it['work_item_id']}.json").read_text())
    pts = pd.DataFrame(s["points"])
    hours = pd.to_datetime(pts["t"]).dt.hour
    fig, ax = plt.subplots(figsize=(8, 3.8))
    ax.fill_between(hours, pts["low"], pts["high"], color=S1, alpha=0.18, linewidth=0, label="interval P10-P90")
    ax.plot(hours, pts["expected"], color=S1, label="P50 prezis")
    if pts["value"].notna().any():
        ax.plot(hours, pts["value"], color=S2, label="simularea fizică")
    ax.axhline(LIMIT, color=INK2, lw=1, ls="--")
    ax.text(0.2, LIMIT + 0.002, "limita 1,10 pu", color=INK2, fontsize=8)
    ax.set_xlabel("ora")
    ax.set_ylabel("tensiunea maximă pe post (pu)")
    ax.set_title(f"{it['asset_id']}, {it['target_date']}: tensiunea oră cu oră (post sintetic)", loc="left")
    ax.legend(loc="upper left", ncols=3)
    ax.set_xticks(range(0, 24, 2))
    _save(fig, f"series_{scenario}.png")


def ladder(scenario: str = "demo-vara", post_id: str = "PT-1252") -> None:
    """Scara de soluții pentru un post: P90 după fiecare treaptă și după combinația aleasă, cu costul."""
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    from cyberpunks.c_prosumatori.remedies import ACTION_RO

    short = {"phase_rebalance": "faze", "adjust_tap": "priză", "notify_customers": "mesaje", "offer_battery": "baterii",
             "export_limit": "limită de export", "transformer_upgrade": "post nou"}
    wi = OUTPUTS / "work_items" / scenario / "C.jsonl"
    items = [json.loads(x) for x in wi.read_text().splitlines() if x.strip()]
    it = next((x for x in items if x["asset_id"] == post_id and x["extra"].get("remedy_options")), None)
    if it is None:
        return
    e = it["extra"]
    opts = sorted(e["remedy_options"], key=lambda o: o["cost_lei"])
    base = e["ladder_base_p90_pu"]
    chosen = e["ladder_choice"]
    labels = [ACTION_RO.get(o["action"], o["action"]) for o in opts] + ["aleasă: " + " + ".join(short[a] for a in chosen)]
    vals = [o["p90_after_pu"] for o in opts] + [base + sum(o["effect_pu"] for o in opts if o["action"] in chosen)]
    costs = [o["cost_lei"] for o in opts] + [sum(o["cost_lei"] for o in opts if o["action"] in chosen)]
    colors = [S1] * len(opts) + [S2]
    fig, ax = plt.subplots(figsize=(9.5, 4.4))
    y = np.arange(len(vals))[::-1]
    lo = min(min(vals), 1.08) - 0.005
    hi = max(vals + [base]) + 0.004
    ax.barh(y, [v - lo for v in vals], left=lo, color=colors, height=0.6, edgecolor=SURFACE, linewidth=2)
    ax.axvline(base, color=INK2, lw=1, ls=":")
    ax.axvline(LIMIT, color=INK2, lw=1.2, ls="--")
    for yy, v, c in zip(y, vals, costs, strict=True):  # coloana de etichete, în dreapta graficului
        txt = f"{v:.3f} pu · {c:,.0f} lei".replace(",", "X").replace(".", ",").replace("X", ".")
        ax.text(1.01, yy, txt, va="center", fontsize=8.5, color=INK, transform=ax.get_yaxis_transform(), clip_on=False)
    ax.set_yticks(y, labels)
    ax.set_xlim(lo, hi)
    ax.set_xlabel("tensiunea maximă P90 după soluție (pu)")
    ax.set_title(f"{post_id}, {it['target_date']}: ce aduce tensiunea sub 1,10 pu și cât costă", loc="left")
    ax.grid(axis="y", visible=False)
    ax.legend(handles=[Patch(color=S1, label="o singură treaptă"), Patch(color=S2, label="combinația aleasă"),
                       Line2D([], [], color=INK2, ls="--", label="limita 1,10 pu"), Line2D([], [], color=INK2, ls=":", label="P90 fără soluție")],
              loc="upper center", bbox_to_anchor=(0.45, -0.16), ncols=4, fontsize=8.5)
    fig.text(0.01, -0.12, "Post sintetic; efectele sunt simulate pe rețeaua postului (calcul de rețea), costurile din config/economics.yaml.",
             fontsize=8, color=INK2)
    _save(fig, f"ladder_{scenario}_{post_id}.png")


def main() -> None:
    res = pd.read_parquet(DATA_PROCESSED / "C" / "eval_predictions.parquet")
    detail = json.loads((REPORTS / "C" / "metrics_detail.json").read_text())
    pred_vs_sim(res)
    mae_by_topology(detail)
    reliability(res)
    example_series("demo-vara")
    ladder("demo-vara", "PT-1252")
    print("figuri în", FIG)


if __name__ == "__main__":
    main()
