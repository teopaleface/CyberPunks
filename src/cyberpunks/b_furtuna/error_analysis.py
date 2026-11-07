"""Analiza erorilor modelului B pe anul de test (2025): unde greșește și de ce.

    uv run python -m cyberpunks.b_furtuna.error_analysis
Citește modelul salvat de `evaluate.py` și tabelul comitat × zi. Scrie `reports/B/error_analysis.md`
(partea calculată; secțiunea „Ce am încercat” se completează din `reports/B/experiments.json`).
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

from cyberpunks.b_furtuna import dataset
from cyberpunks.b_furtuna.evaluate import TEST_YEAR
from cyberpunks.b_furtuna.model import BModel
from cyberpunks.common.paths import REPORTS

OUT = REPORTS / "B" / "error_analysis.md"
EXPERIMENTS = REPORTS / "B" / "experiments.json"


# Evenimente reale cunoscute din eșantion, ca verificare a lanțului de date (oră UTC -> zi locală, agregare, vreme).
KNOWN_EVENTS = [
    ("26075", "2023-02-22", "Furtuna de iarnă din februarie 2023, cu gheață: cel puțin 811.000 de întreruperi în Michigan",
     "https://en.wikipedia.org/wiki/February_2023_North_American_winter_storm"),
    ("17033", "2023-03-31", "Valul de tornade din 31 martie - 1 aprilie 2023",
     "https://en.wikipedia.org/wiki/Tornado_outbreak_of_March_31_%E2%80%93_April_1,_2023"),
    ("21005", "2024-09-27", "Resturile uraganului Helene", "https://en.wikipedia.org/wiki/Hurricane_Helene"),
    ("36031", "2023-03-14", "Furtuna de zăpadă din martie 2023 (nor'easter)",
     "https://en.wikipedia.org/wiki/2022%E2%80%9323_North_American_winter"),
    ("21005", "2025-11-12", ("Posibil artefact de date: două comitate vecine (Anderson și Clark, KY) peste 60%, fără vânt "
     "sau ploaie semnificative"), ""),
]


def weather_type(df: pd.DataFrame) -> pd.Series:
    """Tipul de vreme al zilei, după reguli simple (ordinea contează)."""
    t = pd.Series("fără semnal meteo puternic", index=df.index)
    t[df["precip_48h"] >= 30] = "ploaie abundentă (≥ 30 mm în 48 h)"
    t[df["snow_3d"] >= 5] = "zăpadă (≥ 5 cm în 3 zile)"
    t[df["ice_proxy"] >= 2] = "ploaie la sub 0 °C (polei, chiciură)"
    t[df["gust_max_2d"] >= 60] = "vânt (rafale ≥ 60 km/h)"
    return t


def season(m: pd.Series) -> pd.Series:
    return m.map({12: "iarna", 1: "iarna", 2: "iarna", 3: "primăvara", 4: "primăvara", 5: "primăvara",
                  6: "vara", 7: "vara", 8: "vara", 9: "toamna", 10: "toamna", 11: "toamna"})


def table(df: pd.DataFrame, by: str, thr: float) -> pd.DataFrame:
    rows = []
    for k, g in df.groupby(by, observed=True):
        y, p = g["event"].to_numpy(), g["p"].to_numpy()
        ev = y == 1
        rows.append({
            by: k,
            "zile": len(g),
            "evenimente": int(ev.sum()),
            "prevalență": round(float(ev.mean()), 3),
            "PR-AUC": round(float(average_precision_score(y, p)), 3) if 0 < ev.sum() < len(g) else np.nan,
            "recall la prag": round(float((p[ev] >= thr).mean()), 3) if ev.sum() else np.nan,
            "alarme false / 100 zile calme": round(float(100 * (p[~ev] >= thr).mean()), 1) if (~ev).sum() else np.nan,
            "P medie pe evenimente": round(float(p[ev].mean()), 3) if ev.sum() else np.nan,
        })
    return pd.DataFrame(rows)


def fmt_int(n: float) -> str:
    """1234567 -> „1.234.567” (separatorul de mii din română)."""
    return f"{int(n):,}".replace(",", ".")


def md(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join("" if pd.isna(v) else str(v) for v in r.to_numpy()) + " |")
    return "\n".join(lines)


def run() -> str:
    model = BModel.load()
    df = pd.read_parquet(dataset.OUT)
    df["date"] = pd.to_datetime(df["date"])
    summary = json.loads(dataset.SUMMARY.read_text(encoding="utf-8"))
    te = df[(df["year"] == TEST_YEAR) & ~df["wx_missing"]].copy()
    te["p"] = model.predict_proba(te)
    thr = model.decision_threshold
    te["tip"] = weather_type(te)
    te["sezon"] = season(te["date"].dt.month)
    te["mărime"] = pd.qcut(te["customers"], 3, labels=["comitate mici", "comitate medii", "comitate mari"])
    qs = model.predict_quantiles(te)
    te["q10"], te["q50"], te["q90"] = qs[:, 0], qs[:, 1], qs[:, 2]

    parts = [
        "# Analiza erorilor, modelul B (risc de avarii la furtună)",
        "",
        (f"Generat de `uv run python -m cyberpunks.b_furtuna.error_analysis`. Model `{model.version}`, antrenat pe "
        f"{model.train_info['years'][0]}-{model.train_info['years'][-1]}, evaluat pe {TEST_YEAR} ({fmt_int(len(te))} zile-comitat, "
        f"{fmt_int(te['event'].sum())} evenimente). Pragul de decizie: {thr:.2f}."),
        "",
        "## Pe tipuri de vreme",
        "",
        md(table(te, "tip", thr)),
        "",
        "## Pe sezoane",
        "",
        md(table(te, "sezon", thr)),
        "",
        "## Pe mărimea comitatului",
        "",
        md(table(te, "mărime", thr)),
        "",
    ]

    ext = te[te["extreme"] == 1].sort_values("pct_out_max", ascending=False)
    missed = ext[ext["p"] < thr].head(10)
    parts += [
        "## Evenimente extreme (vârf ≥ 10% din clienți)",
        "",
        (f"{len(ext)} evenimente extreme în {TEST_YEAR}; modelul le prinde la prag pe {int((ext['p'] >= thr).sum())} "
        f"({(ext['p'] >= thr).mean():.0%}). P medie: {ext['p'].mean():.2f}."),
        "",
        "Cele mai mari ratate (P sub prag):",
        "",
        md(missed[["county", "state", "date", "pct_out_max", "p", "gust_max", "gust_prev", "precip_48h", "snow_3d",
                   "ice_proxy"]].assign(date=missed["date"].dt.date, pct_out_max=missed["pct_out_max"].round(3),
                                        p=missed["p"].round(3))) if len(missed) else "Niciunul.",
        "",
    ]
    fp = te[(te["event"] == 0)].sort_values("p", ascending=False).head(10)
    parts += [
        "## Cele mai sigure alarme false",
        "",
        md(fp[["county", "state", "date", "pct_out_max", "p", "gust_max", "precip_48h", "snow_3d"]].assign(
            date=fp["date"].dt.date, pct_out_max=fp["pct_out_max"].round(4), p=fp["p"].round(3))),
        "",
    ]
    known_rows = []
    for fips, day, what, url in KNOWN_EVENTS:
        r = df[(df["fips"] == fips) & (df["date"] == pd.Timestamp(day))]
        if r.empty:
            continue
        r = r.iloc[0]
        in_test = int(r["year"]) == TEST_YEAR
        p_txt = f"{float(model.predict_proba(r.to_frame().T.astype({f: float for f in model.features}))[0]):.2f}" \
            if in_test else "an de antrenare"
        known_rows.append({"eveniment": what + (f" ({url})" if url else ""), "comitat": f"{r['county']}, {r['state']}",
                           "ziua": day, "vârf": f"{r['pct_out_max']:.0%}", "rafală": round(float(r["gust_max"])),
                           "ploaie 48 h": round(float(r["precip_48h"]), 1), "ploaie la sub 0 °C": round(float(r["ice_proxy"]), 1),
                           "zăpadă 3 zile": round(float(r["snow_3d"]), 1), "P model": p_txt})
    if known_rows:
        parts += [
            "## Verificare pe evenimente cunoscute",
            "",
            ("Zilele din anii de antrenare arată doar că datele sunt citite corect (ora, ziua, vremea). Nu sunt o evaluare: "
             "modelul le-a văzut."),
            "",
            md(pd.DataFrame(known_rows)),
            "",
        ]
    ev = te[te["event"] == 1]
    inside = ((ev["pct_out_max"] >= ev["q10"]) & (ev["pct_out_max"] <= ev["q90"])).mean()
    above = (ev["pct_out_max"] > ev["q90"]).mean()
    below = (ev["pct_out_max"] < ev["q10"]).mean()
    parts += [
        "## Cuantilele (cât de mare, dacă se întâmplă)",
        "",
        (f"Pe zilele cu eveniment din {TEST_YEAR}: vârful real e în intervalul P10-P90 în {inside:.0%} din cazuri "
        f"(ținta: 80%), peste P90 în {above:.0%}, sub P10 în {below:.0%}."),
        "",
        "## Calitatea datelor",
        "",
        f"- Comitat-ani scoși pentru acoperire EAGLE-I sub 50% din zile: {summary['dropped_low_coverage_county_years']}.",
        f"- Zile scoase pentru valori blocate (același vârf ≥ 0,5% din clienți 4 zile la rând): {summary['dropped_stuck_days']}.",
        f"- Vârfuri peste numărul de clienți (MCC e modelat), tăiate la 100%: {summary['clipped_over_100pct']}.",
        (f"- Rânduri cu vreme lipsă: {summary['rows_missing_weather']}. Probleme de vreme: "
        f"{'; '.join(summary['weather_issues']) or 'niciuna'}."),
        ("- În EAGLE-I, lipsa unui rând înseamnă fie zero clienți afectați, fie o pauză în colectare (Brelsford et al. 2024). "
        "Le tratăm ca zero doar în comitatele cu acoperire bună, așa că o parte din „alarmele false” pot fi avarii nevăzute."),
        "",
    ]
    missed_all = ext[ext["p"] < thr]
    quiet = ((missed_all["gust_max_2d"] < 60) & (missed_all["precip_48h"] < 30) & (missed_all["snow_3d"] < 5)
             & (missed_all["ice_proxy"] < 2))
    quiet_share = float(quiet.mean()) if len(missed_all) else float("nan")
    by_type = table(te, "tip", thr).set_index("tip")
    calm = "fără semnal meteo puternic"
    share_calm = by_type.loc[calm, "evenimente"] / max(by_type["evenimente"].sum(), 1) if calm in by_type.index else float("nan")
    rest = by_type.drop(index=calm, errors="ignore")
    best, worst = rest["PR-AUC"].idxmax(), rest["PR-AUC"].idxmin()
    parts += [
        "## Concluzii (calculate din tabelele de mai sus)",
        "",
        (f"- {share_calm:.0%} din evenimente apar în zile fără semnal meteo puternic (defecte obișnuite). Vremea nu le poate "
         "prezice, iar ele dau plafonul de PR-AUC pe toate zilele."),
        (f"- Cel mai bine merge la „{best}” (PR-AUC {rest.loc[best, 'PR-AUC']:.2f}, recall la prag "
         f"{rest.loc[best, 'recall la prag']:.0%}); cel mai slab la „{worst}” (PR-AUC {rest.loc[worst, 'PR-AUC']:.2f}, "
         f"recall {rest.loc[worst, 'recall la prag']:.0%}). Ninsoarea zilnică nu spune dacă zăpada e grea și udă, adică "
         "felul care rupe liniile."),
        (f"- Evenimentele extreme (≥ 10%): {(ext['p'] >= thr).mean():.0%} prinse la prag. Din cele {len(missed_all)} ratate, "
         f"{(missed_all['gust_max_2d'] < 60).mean():.0%} au rafale sub 60 km/h în arhivă, iar {quiet_share:.0%} nu au niciun "
         "semnal meteo puternic: fie vijelii locale pe care modelul meteo nu le vede, fie cauze fără legătură cu vremea "
         "(defecte, artefacte de date). Nu le putem deosebi fără istoricul de intervenții."),
        (f"- Cuantilele: {inside:.0%} din vârfurile reale în intervalul P10-P90, după calibrarea conformală."),
        "",
    ]
    if EXPERIMENTS.exists():
        exps = json.loads(EXPERIMENTS.read_text(encoding="utf-8"))
        parts += ["## Ce am încercat", "", md(pd.DataFrame(exps)), ""]
    text = "\n".join(parts) + "\n"
    OUT.write_text(text, encoding="utf-8")
    print(f"-> {OUT}")
    return text


if __name__ == "__main__":
    run()
