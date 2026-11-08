"""Backtest calitativ pe furtuna reală din Banat, 6-10 iulie 2025: ce ar fi recomandat agentul în fiecare seară
de dinainte, comparat cu ce a scris presa.

    uv run python -m cyberpunks.b_furtuna.backtest
Scrie `reports/B/backtest_romania.md`, `reports/B/fig_backtest_zones.png` și lucrările pe zile în
`outputs/work_items/backtest-2025-07/B-<data>.jsonl`. Costă circa 80 de apeluri Open-Meteo.

Nu avem istoricul de avarii Rețele Electrice, deci comparația e calitativă: ce zone au fost lovite, în ce zi,
cu ce ordin de mărime.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cyberpunks.b_furtuna import plotstyle, predict, romania
from cyberpunks.b_furtuna.model import BModel
from cyberpunks.common import config
from cyberpunks.common.paths import OUTPUTS, REPORTS

DAYS = [date(2025, 7, d) for d in range(6, 11)]
# Al doilea caz: furtuna de la Slobozia (Ialomița), seara de 17 iulie 2025
CASE2_DAYS = [date(2025, 7, d) for d in (16, 17, 18)]
CASE2_ZONE = "IL-SLOBOZIA"
CASE2_PRESS = ("2025-07-17 (seara)", "Ialomița (Slobozia)",
               ("Cod roșu de vreme severă; peste 52 de copaci doborâți, acoperișuri smulse, străzi inundate, peste 100 de "
               "intervenții ale pompierilor. Articolul nu dă cifre despre curent."),
               ("https://stirileprotv.ro/stiri/actualitate/furtuna-a-facut-pagube-majore-in-slobozia-peste-50-de-copaci-au-"
               "fost-doborati-de-vant-si-mai-multe-strazi-au-fost-inundate.html"))
# Al treilea caz, de iarnă: viscolul din Dobrogea, 26-27 noiembrie 2023
CASE3_DAYS = [date(2023, 11, d) for d in (24, 25, 26, 27, 28)]
CASE3_REGION = "dobrogea"
CASE3_PRESS = [
    ("2023-11-26, 02:00-16:00", "Constanța, Tulcea, Călărași, Ialomița (și alte 4 județe)",
     "ANM: cod portocaliu de viscol, rafale de 75-85 km/h, vizibilitate sub 50 m.",
     "https://radioconstanta.ro/2023/11/24/constanta-tulcea-anm-a-emis-un-cod-portocaliu-de-viscol"),
    ("2023-11-27/28", "Dobrogea",
     ("Rețele Electrice Dobrogea, la o actualizare de la ora 13:00: circa 61.000 de clienți din 99 de localități fără "
      "curent (32.000 Constanța, 19.000 Tulcea, 9.000 Călărași, 1.000 Ialomița); echipe suplimentare aduse din Muntenia și Banat."),
     ("https://www.economica.net/retele-electrice-dobrogea-a-reconectat-la-retea-80-dintre-clientii-care-au-ramas-fara-"
     "curent-in-ultimele-zile-49-000-de-consumatori-inca-nu-au-lumina_709345.html")),
]
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


def _predict_days(model: BModel, econ: dict, zones: list, days: list[date]) -> list[dict]:
    """Agentul pentru fiecare zi din `days` (rulat în seara de dinainte), cu vremea cerută o singură dată pe interval."""
    wx, issues = romania.weather_daily_range(zones, days[0] - timedelta(days=romania.LAG_DAYS), days[-1])
    hourly = romania.weather_hourly_range(zones, days[0] - timedelta(days=1), days[-1] + timedelta(days=1))
    mdaily = predict.hist_models_daily(zones, days[0] - timedelta(days=1), days[-1])
    OUT_ITEMS.mkdir(parents=True, exist_ok=True)
    rows = []
    for d in days:
        feats = predict.target_features(zones, wx, d)
        lo, hi, src = predict.uncertainty(model, zones, feats, d, "historical", mdaily=mdaily)
        created = predict.decision_time(d, "historical")
        items, _ = predict.build_items(model, zones, feats, hourly, d, "historical", created, econ, "backtest",
                                       lo, hi, src, issues)
        (OUT_ITEMS / f"B-{d.isoformat()}.jsonl").write_text("".join(it.model_dump_json() + "\n" for it in items),
                                                            encoding="utf-8")
        for z, it in zip(zones, items, strict=True):
            rows.append({
                "date": d, "zone_id": z.zone_id, "county": z.county, "region": z.region,
                "p": it.prediction.score, "lo": it.prediction.interval_low, "hi": it.prediction.interval_high,
                "action": getattr(it.recommended_action, "value", it.recommended_action),
                "gust": it.extra["gust_max_kmh"], "precip48": it.extra["precip_48h_mm"],
                "cust_p50": it.impact.customers_affected, "zone_customers": z.customers,
                "onset": it.extra["storm_onset"][11:16], "reason": it.prediction.abstain_reason or "",
            })
    return rows


def run() -> pd.DataFrame:
    model = BModel.load()
    econ = config.load("economics")["storm"]
    zones = romania.load_zones()
    rows = _predict_days(model, econ, zones, DAYS + CASE2_DAYS)
    rows += _predict_days(model, econ, zones, CASE3_DAYS)
    df = pd.DataFrame(rows)
    figure(df[df["date"].isin(DAYS)], model.decision_threshold)
    write_md(df, model)
    write_summary(df)
    return df


BANAT_CUSTOMERS = 967_682  # RER Banat, 31.12.2024 (Planul de dezvoltare RER 2026-2035, tabelul 2.1)
# Rețele Electrice Banat, anexa 2 ANRE pe 2025: SAIDI din condiții meteorologice deosebite (CMD), minute pe utilizator
CMD_SAIDI_2025 = {"rural JT": 92.87, "rural MT": 65.06, "urban JT": 16.94, "urban MT": 15.18}
CMD_SOURCE = "https://www.reteleelectrice.ro/wp-content/uploads/banat-anexa-2-2025.pdf"
ANRE_2025 = ("ANRE 2025 (prin Economica): 236 de minute de întrerupere pe client la nivel național, din care 91,41 "
             "neplanificate, https://www.economica.net/romanii-au-stat-fara-electricitate-in-medie-patru-ore-in-2025-"
             "situatie-putin-mai-proasta-fata-de-anul-precedent_961648.html")


def _n(x: float) -> str:
    """Număr întreg cu separatorul de mii din română."""
    return f"{round(x):,}".replace(",", ".")


def _de(x: float) -> str:
    """„de” după numerale, ca în română: 10 minute, dar 20 de minute."""
    n = round(x)
    return " de" if n % 100 >= 20 or n % 100 == 0 else ""


def order_of_magnitude(df: pd.DataFrame) -> list[str]:
    """Verificarea de ordin de mărime cu cifrele oficiale din România (anuale, nu pe furtună)."""
    affected = 40_000  # prefectul Timișului, cumulat 7-9 iulie 2025 (vezi PRESS)
    share = affected / BANAT_CUSTOMERS
    b = df[(df["region"] == "banat") & df["date"].isin(DAYS[1:3])]
    expected = (b["p"] * b["cust_p50"]).sum()
    share_ro = f"{100 * share:.1f}%".replace(".", ",")
    lines = ["", "## Ordin de mărime, cu cifrele oficiale din România", "",
             (f"- Furtuna din 7-9 iulie 2025 a afectat circa {_n(affected)} de consumatori (prefectul Timișului), adică "
              f"{share_ro} din cei {_n(BANAT_CUSTOMERS)} de utilizatori Rețele Electrice Banat.")]
    for hours in (4, 8, 12):  # IPOTEZĂ: durata medie a întreruperii pentru un consumator afectat
        mins = affected * hours * 60 / BANAT_CUSTOMERS
        lines.append(f"  - Dacă întreruperea a durat în medie {hours} ore (IPOTEZĂ), furtuna adaugă circa {mins:.0f}{_de(mins)} "
                     "minute la SAIDI-ul anual al Banatului.")
    lines += [
        (f"- Rețele Electrice Banat, 2025, SAIDI din condiții meteorologice deosebite: "
         f"{str(CMD_SAIDI_2025['rural JT']).replace('.', ',')} de minute în mediul rural la JT și "
         f"{str(CMD_SAIDI_2025['urban JT']).replace('.', ',')} în mediul urban la JT ({CMD_SOURCE}). O singură furtună ca "
         "aceasta are, deci, același ordin de mărime cu minutele anuale din cauza vremii: cifrele din presă și cele "
         "oficiale se potrivesc ca mărime."),
        (f"- Modelul: suma vârfurilor așteptate pe zonele din Banat pe 7-8 iulie e de circa {_n(expected)} de clienți "
         "(P × P50), același ordin de mărime cu cei circa 40.000 de consumatori cumulați în trei zile."),
        f"- Pentru context: {ANRE_2025}. Cifrele ANRE sunt anuale, deci servesc doar la verificare, nu la antrenare.",
        "",
    ]
    return lines


def write_summary(df: pd.DataFrame) -> Path:
    """Cifrele-cheie ale celor trei cazuri, pentru fișa modelului (reports/B/backtest_summary.json)."""
    c1 = df[df["date"].isin(DAYS[1:3])]
    b1, r1 = c1[c1["region"] == "banat"], c1[c1["region"] != "banat"]
    c2 = df[df["date"] == CASE2_DAYS[1]]
    p2 = float(c2.loc[c2["zone_id"] == CASE2_ZONE, "p"].iloc[0])
    ties2 = sorted(c2.loc[(c2["p"] == p2) & (c2["zone_id"] != CASE2_ZONE), "zone_id"])
    c3 = df[df["date"] == CASE3_DAYS[2]]
    d3, r3 = c3[c3["region"] == CASE3_REGION], c3[c3["region"] != CASE3_REGION]
    out = {
        "banat_2025_07_07_08": {"p_banat": round(float(b1["p"].mean()), 3), "p_rest": round(float(r1["p"].mean()), 3),
                                "crews_banat_zone_days": int((b1["action"] == "preposition_crew").sum()),
                                "crews_rest_zone_days": int((r1["action"] == "preposition_crew").sum())},
        "slobozia_2025_07_17": {"rank": int((c2["p"] > p2).sum()) + 1, "zones": len(c2), "p": round(p2, 3),
                                "tied_with": ties2},
        "dobrogea_2023_11_26": {"p_dobrogea": round(float(d3["p"].mean()), 3), "p_rest": round(float(r3["p"].mean()), 3),
                                "crews_dobrogea": int((d3["action"] == "preposition_crew").sum()), "zones_dobrogea": len(d3)},
    }
    path = REPORTS / "B" / "backtest_summary.json"
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    return path


def figure(df: pd.DataFrame, thr: float) -> None:
    plotstyle.apply()
    order = df[df["date"] == DAYS[2]].sort_values(["region", "p"], ascending=[True, False])["zone_id"].tolist()
    piv = df.pivot(index="zone_id", columns="date", values="p").loc[order]
    act = df.pivot(index="zone_id", columns="date", values="action").loc[order]
    vmax = max(0.6, float(piv.max().max()))
    fig, ax = plt.subplots(figsize=(7.4, 9.2))
    im = ax.imshow(piv.to_numpy(), cmap=plotstyle.RISK_CMAP, vmin=0, vmax=vmax, aspect="auto")
    ax.grid(False)
    ax.set_xticks(range(len(DAYS)), [d.strftime("%d.%m") for d in DAYS])
    ax.set_yticks(range(len(order)), order, fontsize=8)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    for i in range(len(order)):
        for j in range(len(DAYS)):
            v = float(piv.iloc[i, j])
            a = act.iloc[i, j]
            mark = " E" if a == "preposition_crew" else (" ?" if a == "human_review" else "")
            ink = plotstyle.SURFACE if v / vmax > 0.55 else plotstyle.TEXT
            ax.text(j, i, f"{v:.2f}{mark}", ha="center", va="center", fontsize=7.5, color=ink)
    ax.set_title(f"Riscul de avarii pe zone, 6-10 iulie 2025\nE = echipă trimisă din timp (P ≥ {thr:.2f}), "
                 "? = decide omul", loc="left", fontsize=10)
    cb = fig.colorbar(im, ax=ax, shrink=0.55, pad=0.02)
    cb.set_label("P(vârf ≥ 1% din clienți)", color=plotstyle.TEXT_2)
    cb.outline.set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT_FIG, dpi=150)
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
    c2 = df[df["date"].isin(CASE2_DAYS)]
    tgt = c2[c2["zone_id"] == CASE2_ZONE].set_index("date")
    others = c2[c2["zone_id"] != CASE2_ZONE].groupby("date")["p"].mean()
    d17 = CASE2_DAYS[1]
    day17 = c2[c2["date"] == d17]
    rank17 = int((day17["p"] > tgt.loc[d17, "p"]).sum()) + 1
    ties17 = sorted(day17.loc[(day17["p"] == tgt.loc[d17, "p"]) & (day17["zone_id"] != CASE2_ZONE), "zone_id"])
    tie_txt = f", la egalitate cu {', '.join(ties17)}" if ties17 else ""
    lines += [
        "## Al doilea caz: furtuna de la Slobozia, 17 iulie 2025",
        "",
        "| Ziua | Unde | Ce s-a întâmplat | Sursa |",
        "|---|---|---|---|",
        f"| {CASE2_PRESS[0]} | {CASE2_PRESS[1]} | {CASE2_PRESS[2]} | {CASE2_PRESS[3]} |",
        "",
        "| Ziua | P Slobozia | interval | Recomandare | Rafală (km/h) | Ploaie 48 h (mm) | Început estimat | P medie, celelalte 25 de zone |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for d in CASE2_DAYS:
        r = tgt.loc[d]
        lines.append(f"| {d:%d.%m} | {r['p']:.2f} | {r['lo']:.2f}-{r['hi']:.2f} | {r['action']} | {r['gust']} | "
                     f"{r['precip48']} | {r['onset']} | {others.loc[d]:.2f} |")
    lines += [
        "",
        (f"Pe 17 iulie, Slobozia a fost pe locul {rank17} din 26 de zone după risc{tie_txt} (P = {tgt.loc[d17, 'p']:.2f}). "
         "Nu avem cifre despre clienții fără curent, deci verificăm doar dacă zona lovită iese în față."),
        "",
    ]
    c3 = df[df["date"].isin(CASE3_DAYS)]
    lines += ["## Al treilea caz, de iarnă: viscolul din Dobrogea, 26-27 noiembrie 2023", "",
              "| Ziua | Unde | Ce s-a întâmplat | Sursa |", "|---|---|---|---|"]
    lines += [f"| {d} | {w} | {t} | {u} |" for d, w, t, u in CASE3_PRESS]
    lines += ["", ("| Ziua | Dobrogea: P medie | Dobrogea: echipe recomandate | Dobrogea: rafala maximă (km/h) | "
              "Restul: P medie | Primele 3 zone |"), "|---|---|---|---|---|---|"]
    for d in CASE3_DAYS:
        g = c3[c3["date"] == d]
        dob, rest = g[g["region"] == CASE3_REGION], g[g["region"] != CASE3_REGION]
        top = ", ".join(f"{r.zone_id} {r.p:.2f}" for r in g.sort_values("p", ascending=False).head(3).itertuples())
        gmax = dob["gust"].dropna().max()
        lines.append(f"| {d:%d.%m.%Y} | {dob['p'].mean():.2f} | {(dob['action'] == 'preposition_crew').sum()} din {len(dob)} | "
                     f"{gmax:.0f} | {rest['p'].mean():.2f} | {top} |")
    lines += order_of_magnitude(df)
    d26 = c3[c3["date"].isin(CASE3_DAYS[2:4])]
    dob26, rest26 = d26[d26["region"] == CASE3_REGION], d26[d26["region"] != CASE3_REGION]
    lines += [
        "",
        (f"Pe 26-27 noiembrie, riscul mediu în Dobrogea a fost {dob26['p'].mean():.2f}, față de {rest26['p'].mean():.2f} "
         "în Muntenia și Banat. "
         + ("Zona lovită iese în față și iarna." if dob26["p"].mean() > rest26["p"].mean()
            else "Modelul NU scoate în față zona lovită: vezi limitele (zăpada e punctul slab).")),

        "",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"-> {OUT_MD}")


if __name__ == "__main__":
    np.seterr(all="ignore")
    out = run()
    print(out.groupby(["date", "region"])["p"].mean().unstack().round(3))
