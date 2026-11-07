"""Figurile pentru prezentare (reports/A/figures/), desenate din cifrele scripturilor (metrics_full.json).

    uv run python -m cyberpunks.a_contoare.figures

- headline_precision.png: câte din primele K contoare verificate au o problemă reală: furt real (SGCC), probleme
  subtile și toate problemele (Londra, sintetic), modelul față de regula simplă și regula VEE completă;
- ranking_at_k.png: precizia și recall-ul la mai multe valori K (nu depindem de un singur K);
- false_alarms_by_consumption.png: alarmele false pe chintile de consum (etica: consumul mic nu e dovadă).

Paleta e validată (skill-ul dataviz: primele 3 sloturi, toate perechile, inclusiv daltonism); valorile se scriu
direct pe bare, pentru că verdele-turcoaz are contrast mic față de fundal.
"""

from __future__ import annotations

import json
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from cyberpunks.common.paths import REPORTS

REP = REPORTS / "A"
FIG = REP / "figures"
SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
SERIES = {  # ordinea fixă din paleta validată
    "model": ("#2a78d6", "Modelul nostru (LightGBM)"),
    "rule": ("#eb6834", "Regula simplă (zero 7 zile sau scădere 50%)"),
    "vee": ("#1baf7a", "Regula VEE completă (folosită azi de utilități)"),
}


def ro(x: float, nd: int = 2) -> str:
    return f"{x:.{nd}f}".replace(".", ",")


def _style(ax, ylabel: str | None = None) -> None:
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS)
    ax.tick_params(colors=MUTED, labelsize=10)
    ax.yaxis.grid(True, color=GRID, linewidth=1, linestyle="-")
    ax.set_axisbelow(True)
    if ylabel:
        ax.set_ylabel(ylabel, color=INK2, fontsize=11)


def _title(fig, title: str, subtitle: str) -> None:
    fig.suptitle(title, x=0.01, y=0.985, ha="left", fontsize=15, fontweight="bold", color=INK)
    fig.text(0.01, 0.94, subtitle, ha="left", va="top", fontsize=10.5, color=INK2, linespacing=1.4)


def headline(full: dict) -> None:
    S, L = full["sgcc_real_labels"], full["lcl_injected"]
    sub = L["subtle_only"]
    groups = [
        (f"Furt real\nSGCC, {format(S['n'], ',').replace(',', '.')} de clienți nevăzuți", S),
        ("Probleme subtile\nLondra, fără defectele evidente", sub),
        ("Toate problemele\nLondra (vârful listei = defecte evidente)", L),
    ]
    fig, ax = plt.subplots(figsize=(12, 6.2), facecolor=SURFACE)
    _style(ax, "Precizia@K (câte vizite găsesc o problemă reală)")
    width = 0.24
    x = np.arange(len(groups))
    for j, (key, (color, label)) in enumerate(SERIES.items()):
        vals = [g[1][key]["precision_at_k"] for g in groups]
        bars = ax.bar(x + (j - 1) * width, vals, width, color=color, label=label, edgecolor=SURFACE, linewidth=2)
        for b, v in zip(bars, vals, strict=True):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.015, ro(v), ha="center", va="bottom", fontsize=11,
                    color=INK, fontweight="bold" if key == "model" else "normal")
    ax.set_xticks(x, [g[0] for g in groups], fontsize=11, color=INK2)
    ax.set_ylim(0, 1.12)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0], ["0", "0,25", "0,50", "0,75", "1,00"])
    ax.legend(loc="upper left", frameon=False, fontsize=10, labelcolor=INK2, ncols=3, bbox_to_anchor=(0, 1.02))
    _title(fig, "Din primele K contoare trimise la verificare, câte au o problemă reală?",
           "K = 1% din contoare (cam o săptămână de vizite pentru 3 echipe la 10.000 de contoare).\n"
           "Seturi de test separate: clienți și gospodării nevăzute la antrenare. Londra = probleme injectate de noi (sintetic).")
    fig.tight_layout(rect=(0, 0, 1, 0.87))
    fig.savefig(FIG / "headline_precision.png", dpi=160, facecolor=SURFACE)
    plt.close(fig)


def ranking(full: dict) -> None:
    panels = [("Furt real (SGCC)", full["sgcc_real_labels"]), ("Londra, probleme injectate (sintetic)",
                                                                full["lcl_injected"])]
    fig, axes = plt.subplots(2, 2, figsize=(12, 7.6), facecolor=SURFACE, sharex="col")
    for col, (name, res) in enumerate(panels):
        cur = res["k_curve"]
        ks = np.array(cur["k"])
        k1, pos = res["k"], cur["positives"]
        for row, metric in enumerate(("precision", "recall")):
            ax = axes[row, col]
            _style(ax, ("Precizia@K" if metric == "precision" else "Recall@K") if col == 0 else None)
            for key, (color, label) in SERIES.items():
                ax.plot(ks, cur[key][metric], color=color, linewidth=2, label=label, solid_capstyle="round")
            for kv, txt in ((k1, "K = 1%"), (pos, "K = numărul de probleme")):
                ax.axvline(kv, color=MUTED, linewidth=1)
                if row == 0:
                    ax.text(kv, 1.03, txt, color=INK2, fontsize=9, ha="center", va="bottom")
            ax.set_ylim(0, 1.0)
            ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0], ["0", "0,25", "0,50", "0,75", "1,00"])
            if row == 1:
                ax.set_xlabel("K = câte contoare verifică echipele", color=INK2, fontsize=10.5)
            if row == 0:
                ax.set_title(name, color=INK, fontsize=12, loc="left", pad=18)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper left", bbox_to_anchor=(0.01, 0.875), ncols=3, frameon=False, fontsize=9.5,
               labelcolor=INK2)
    _title(fig, "Clasamentul la mai multe valori K: modelul rămâne peste reguli pe toată lungimea listei",
           "Sus: ce parte din vizite găsesc o problemă. Jos: ce parte din toate problemele sunt găsite.\n"
           "Test separat; Londra = probleme injectate de noi (sintetic).")
    fig.tight_layout(rect=(0, 0, 1, 0.84))
    fig.savefig(FIG / "ranking_at_k.png", dpi=160, facecolor=SURFACE)
    plt.close(fig)


def false_alarms(full: dict) -> None:
    S, L = full["sgcc_real_labels"], full["lcl_injected"]
    panels = [
        ("Londra (sintetic)", L["false_alarms_by_level"], L["false_alarms_by_level_rule"]),
        ("Furt real (SGCC)", S["false_alarms_by_level"], S.get("false_alarms_by_level_rule", [])),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.6), facecolor=SURFACE, sharey=True)
    width = 0.36
    for ax, (name, model_rows, rule_rows) in zip(axes, panels, strict=True):
        _style(ax, "Alarme false (% din contoarele fără problemă)" if ax is axes[0] else None)
        q = np.arange(1, len(model_rows) + 1)
        for j, (key, rows) in enumerate((("model", model_rows), ("rule", rule_rows))):
            if not rows:
                continue
            color, label = SERIES[key]
            vals = [100 * r["false_alarm_rate"] for r in rows]
            bars = ax.bar(q + (j - 0.5) * width, vals, width, color=color, label=label, edgecolor=SURFACE, linewidth=2)
            for bi in (0, len(bars) - 1):  # etichete doar pe capete: acolo e întrebarea de etică
                b = bars[bi]
                ax.text(b.get_x() + b.get_width() / 2, vals[bi] + 0.3, f"{ro(vals[bi], 1)}%", ha="center",
                        va="bottom", fontsize=10, color=INK)
        ax.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(5))
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
        labels = [f"{r['quintile']}\n{ro(r['level_kwh_median'], 1)} kWh/zi" for r in model_rows]
        ax.set_xticks(q, labels, fontsize=9.5, color=INK2)
        ax.set_xlabel("Chintila de consum (1 = cel mai mic)", color=INK2, fontsize=10.5)
        ax.set_title(name, color=INK, fontsize=12, loc="left")
    axes[0].legend(loc="upper right", frameon=False, fontsize=9.5, labelcolor=INK2)
    sq1_rule = 100 * S.get("false_alarms_by_level_rule", [{}])[0].get("false_alarm_rate", float("nan"))
    sq1_model = 100 * S["false_alarms_by_level"][0]["false_alarm_rate"]
    _title(fig, "Alarmele false pe nivel de consum: consumul mic nu e dovadă de furt",
           "Alarmă falsă = un contor fără problemă ajunge în primele 5% din clasament.\n"
           f"Pe furt real (SGCC), regula simplă trimite echipa la {ro(sq1_rule, 1)}% dintre consumatorii foarte mici fără "
           f"problemă, modelul la {ro(sq1_model, 1)}%.\n"
           "La Londra, cei mai mici consumatori au totuși mai multe alarme false: furtul suspectat acolo merge întâi la un om.")
    fig.tight_layout(rect=(0, 0, 1, 0.80))
    fig.savefig(FIG / "false_alarms_by_consumption.png", dpi=160, facecolor=SURFACE)
    plt.close(fig)


def main() -> int:
    full = json.loads((REP / "metrics_full.json").read_text(encoding="utf-8"))
    FIG.mkdir(parents=True, exist_ok=True)
    headline(full)
    ranking(full)
    false_alarms(full)
    for n in ("headline_precision", "ranking_at_k", "false_alarms_by_consumption"):
        print(f"scris: {FIG / (n + '.png')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
