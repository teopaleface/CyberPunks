"""Backtest calitativ pe furtuna reală din Banat, 6-10 iulie 2025: ce ar fi recomandat agentul în fiecare seară
de dinainte, comparat cu ce a scris presa.

    uv run python -m cyberpunks.b_furtuna.backtest
Scrie `reports/B/backtest_romania.md`, `reports/B/fig_backtest_zones.png` și lucrările pe zile în
`outputs/work_items/backtest-2025-07/B-<data>.jsonl`. Costă circa 80 de apeluri Open-Meteo.

Nu avem istoricul de avarii Rețele Electrice, deci comparația e calitativă: ce zone au fost lovite, în ce zi,
cu ce ordin de mărime.
"""

from __future__ import annotations

from datetime import date, timedelta

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cyberpunks.b_furtuna import predict, romania
from cyberpunks.b_furtuna.model import BModel
from cyberpunks.common import config
from cyberpunks.common.paths import OUTPUTS, REPORTS

DAYS = [date(2025, 7, d) for d in range(6, 11)]
OUT_MD = REPORTS / "B" / "backtest_romania.md"
OUT_FIG = REPORTS / "B" / "fig_backtest_zones.png"
OUT_ITEMS = OUTPUTS / "work_items" / "backtest-2025-07"

# Ce a scris presa (cu sursa). Doar fapte verificate în articole; vezi docs/research/B.md, secțiunea 3.
PRESS = [
    ("2025-07-07", "Caraș-Severin", ("Furtună la Reșița (rețeaua de tramvai ruptă) și la Caransebeș (acoperiș smuls, "
     "rafale de peste 80 km/h)."), "https://tvrinfo.ro/?p=548910"),
    ("2025-07-08", "Timiș, Arad, Caraș-Severin, Hunedoara", ("ANM: cod roșu de vijelii 15:00-21:00, rafale de 90-110 km/h. "
     "Transelectrica: rafale de 90-120 km/h, stâlpi avariați pe linia de 220 kV Reșița-Timișoara."),
     ("https://a1.ro/news/vremea/cod-rosu-de-vijelii-puternice-in-10-judete-din-tara-ce-zone-sunt-afectate-de-ploaia-"
     "torentiala-grindina-si-vant-dupa-canicula-id1139539.html ; https://hotnews.ro/?p=2020474")),
    ("2025-07-07..09", "Timiș (și Banat)", ("Prefectul Timișului: circa 40.000 de consumatori afectați în 82 de localități, "
     "cumulat; 80 de echipe Rețele Electrice și contractori pe teren în Timiș, Arad, Hunedoara, Caraș-Severin."),
     "https://www.pressalert.ro/2025/07/stalpi-de-inalta-tensiune-doborati-de-furtunile-din-ultimele-zile-in-timis/"),
    ("2025-07-08", "București, Ilfov, Giurgiu, Ialomița, Călărași", ("ANM: cod roșu de caniculă (38-41 °C); nicio furtună "
     "raportată."), ("https://a1.ro/news/vremea/cod-rosu-de-vijelii-puternice-in-10-judete-din-tara-ce-zone-sunt-afectate-de-"
     "ploaia-torentiala-grindina-si-vant-dupa-canicula-id1139539.html")),
]


def run() -> pd.DataFrame:
    model = BModel.load()
    econ = config.load("economics")["storm"]
    zones = romania.load_zones()
    wx, issues = romania.weather_daily_range(zones, DAYS[0] - timedelta(days=romania.LAG_DAYS), DAYS[-1])
    hourly = romania.weather_hourly_range(zones, DAYS[0] - timedelta(days=1), DAYS[-1] + timedelta(days=1))
    mdaily = predict.hist_models_daily(zones, DAYS[0] - timedelta(days=1), DAYS[-1])
    OUT_ITEMS.mkdir(parents=True, exist_ok=True)
    rows = []
    for d in DAYS:
        feats = predict.target_features(zones, wx, d)
        lo, hi, src = predict.uncertainty(model, zones, feats, d, "historical", mdaily=mdaily)
        created = predict.decision_time(d, "historical")
        items, _ = predict.build_items(model, zones, feats, hourly, d, "historical", created, econ, "backtest-2025-07",
                                       lo, hi, src, issues)
        (OUT_ITEMS / f"B-{d.isoformat()}.jsonl").write_text("".join(it.model_dump_json() + "\n" for it in items),
                                                            encoding="utf-8")
        for z, it in zip(zones, items, strict=True):
            rows.append({
                "date": d, "zone_id": z.zone_id, "county": z.county, "region": z.region,
                "p": it.prediction.score, "lo": it.prediction.interval_low, "hi": it.prediction.interval_high,
                "action": it.recommended_action, "gust": it.extra["gust_max_kmh"], "precip48": it.extra["precip_48h_mm"],
                "cust_p50": it.impact.customers_affected, "zone_customers": z.customers,
                "onset": it.extra["storm_onset"][11:16], "reason": it.prediction.abstain_reason or "",
            })
    df = pd.DataFrame(rows)
    figure(df, model.decision_threshold)
    write_md(df, model)
    return df


def figure(df: pd.DataFrame, thr: float) -> None:
    order = df[df["date"] == DAYS[2]].sort_values(["region", "p"], ascending=[True, False])["zone_id"].tolist()
    piv = df.pivot(index="zone_id", columns="date", values="p").loc[order]
    act = df.pivot(index="zone_id", columns="date", values="action").loc[order]
    fig, ax = plt.subplots(figsize=(7.5, 9))
    im = ax.imshow(piv.to_numpy(), cmap="OrRd", vmin=0, vmax=max(0.6, float(piv.max().max())), aspect="auto")
    ax.set_xticks(range(len(DAYS)), [d.strftime("%d.%m") for d in DAYS])
    ax.set_yticks(range(len(order)), order, fontsize=8)
    for i in range(len(order)):
        for j in range(len(DAYS)):
            a = act.iloc[i, j]
            mark = "E" if a == "preposition_crew" else ("?" if a == "human_review" else "")
            ax.text(j, i, f"{piv.iloc[i, j]:.2f}{(' ' + mark) if mark else ''}", ha="center", va="center", fontsize=7,
                    color="black")
    ax.set_title(f"Risc de avarii pe zone, 6-10 iulie 2025\nE = echipă trimisă din timp (P ≥ {thr:.2f}), ? = decide omul",
                 fontsize=10)
    fig.colorbar(im, ax=ax, shrink=0.6, label="P(vârf ≥ 1% din clienți)")
    fig.tight_layout()
    fig.savefig(OUT_FIG, dpi=130)
    plt.close(fig)


def write_md(df: pd.DataFrame, model: BModel) -> None:
    thr = model.decision_threshold
    lines = [
        "# Backtest în România: furtuna din Banat, 6-10 iulie 2025",
        "",
        "Generat de `uv run python -m cyberpunks.b_furtuna.backtest`. Pentru fiecare zi, agentul rulează în seara de "
        "dinainte, la 18:00, cu vremea zilei din arhiva Open-Meteo (aceeași sursă ca la antrenare). Incertitudinea vine "
        "din trei modele de prognoză (ICON, ECMWF IFS, GFS). Model: `" + model.version + f"`, prag {thr:.2f}.",
        "",
        ("**Limita:** nu avem istoricul de avarii Rețele Electrice. Comparăm cu presa: ce zone, ce zi, ce ordin de mărime. "
        "Modelul e validat pe date externe (SUA, EAGLE-I) și trebuie calibrat pe istoricul RER."),
        "",
        "## Ce a scris presa",
        "",
        "| Ziua | Unde | Ce s-a întâmplat | Sursa |",
        "|---|---|---|---|",
    ]
    lines += [f"| {d} | {w} | {t} | {s} |" for d, w, t, s in PRESS]
    lines += ["", "## Ce ar fi recomandat agentul", "",
              ("| Ziua | Banat: P medie | Banat: echipe recomandate | Banat: la om | Restul (14 zone): P medie | "
              "Restul: echipe recomandate | Clienți așteptați în Banat (Σ P × P50) |"),
              "|---|---|---|---|---|---|---|"]
    for d in DAYS:
        g = df[df["date"] == d]
        b, r = g[g["region"] == "banat"], g[g["region"] != "banat"]
        exp = int((b["p"] * b["cust_p50"]).sum())
        lines.append(f"| {d:%d.%m} | {b['p'].mean():.2f} | {(b['action'] == 'preposition_crew').sum()} din {len(b)} | "
                     f"{(b['action'] == 'human_review').sum()} | {r['p'].mean():.2f} | "
                     f"{(r['action'] == 'preposition_crew').sum()} din {len(r)} | {exp:,} |".replace(",", "."))
    for d in (DAYS[1], DAYS[2]):
        g = df[df["date"] == d].sort_values("p", ascending=False).head(8)
        lines += ["", f"### {d:%d.%m.%Y}: primele 8 zone după risc", "",
                  ("| Zona | Județ | P | interval | Recomandare | Rafală (km/h) | Ploaie 48 h (mm) | Început estimat | "
                  "Clienți la vârf (P50) |"), "|---|---|---|---|---|---|---|---|---|"]
        for _, r in g.iterrows():
            lines.append(f"| {r['zone_id']} | {r['county']} | {r['p']:.2f} | {r['lo']:.2f}-{r['hi']:.2f} | {r['action']} | "
                         f"{r['gust']} | {r['precip48']} | {r['onset']} | {r['cust_p50']:,} |".replace(",", "."))
    banat_78 = df[(df["region"] == "banat") & df["date"].isin(DAYS[1:3])]
    rest_78 = df[(df["region"] != "banat") & df["date"].isin(DAYS[1:3])]
    pb, pr = banat_78["p"].mean(), rest_78["p"].mean()
    order_ok = pb > pr
    gmin, gmax = banat_78["gust"].min(), banat_78["gust"].max()
    lines += [
        "",
        "## Verdict (calculat)",
        "",
        (f"- Pe 7 și 8 iulie, riscul mediu în Banat a fost {pb:.2f}, față de {pr:.2f} în Muntenia și Dobrogea (caniculă, "
         "fără furtuni raportate). "
         + ("Ordinea regiunilor e aceeași ca în presă." if order_ok else "Ordinea regiunilor NU se potrivește cu presa.")),
        (f"- Echipe recomandate în Banat pe 7-8 iulie: {(banat_78['action'] == 'preposition_crew').sum()} zone-zi; "
         f"în restul țării: {(rest_78['action'] == 'preposition_crew').sum()} zone-zi."),
        (f"- Rafalele din arhivă în Banat pe 7-8 iulie: {gmin:.0f}-{gmax:.0f} km/h, față de 90-120 km/h măsurate: modelele "
         "meteo netezesc vijeliile. Modelul a învățat pe aceeași vreme netezită, deci poate ordona zonele, dar mărimea "
         "locală a vijeliei rămâne incertă."),
        ("- Ordin de mărime: presa dă circa 40.000 de consumatori afectați în Timiș în trei zile (cumulat). Coloana "
         "„clienți așteptați” e suma vârfurilor așteptate pe zonele din Banat, deci se compară doar ca ordin de mărime."),
        "",
        "![Risc pe zone](fig_backtest_zones.png)",
        "",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"-> {OUT_MD}")


if __name__ == "__main__":
    np.seterr(all="ignore")
    out = run()
    print(out.groupby(["date", "region"])["p"].mean().unstack().round(3))
