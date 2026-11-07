"""Generează `reports/B/model_card.md` din fișierele de metrici. Nicio cifră nu e scrisă de mână.

    uv run python -m cyberpunks.b_furtuna.model_card
Citește `reports/B/metrics.json`, `reports/B/metrics_detail.json`, `reports/B/experiments.json`,
`data/processed/B/us_county_day_summary.json` (dacă există) și modelul din `models/release/`.
"""

from __future__ import annotations

import json

from cyberpunks.b_furtuna import dataset
from cyberpunks.b_furtuna.features import FEATURE_SPEC
from cyberpunks.b_furtuna.model import BModel
from cyberpunks.common.paths import REPORTS

OUT = REPORTS / "B" / "model_card.md"


def pct(x: float) -> str:
    return f"{100 * x:.1f}%".replace(".", ",")


def num(x: float, nd: int = 3) -> str:
    return f"{x:.{nd}f}".replace(".", ",")


def ro_int(n: float) -> str:
    return f"{int(n):,}".replace(",", ".")


def run() -> str:
    m = json.loads((REPORTS / "B" / "metrics.json").read_text(encoding="utf-8"))
    d = json.loads((REPORTS / "B" / "metrics_detail.json").read_text(encoding="utf-8"))
    exps = json.loads((REPORTS / "B" / "experiments.json").read_text(encoding="utf-8")) \
        if (REPORTS / "B" / "experiments.json").exists() else []
    summ = json.loads(dataset.SUMMARY.read_text(encoding="utf-8")) if dataset.SUMMARY.exists() else {}
    model = BModel.load()
    mm, bm = m["metrics"], m["baseline_metrics"]
    main = d["main"]
    ti = d["train_info"]
    cap = d.get("capacity", {})
    lo = d.get("loso_summary")

    lines = [
        "# Model card: B, riscul de avarii la furtună",
        "",
        (f"Generat de `uv run python -m cyberpunks.b_furtuna.model_card` din `reports/B/metrics.json` și "
        f"`reports/B/metrics_detail.json`. Versiunea modelului: `{m['model_version']}`, creat la {m['created_at']}."),
        "",
        "## Ce face",
        "",
        ("Estimează, pentru fiecare zonă din aria Rețele Electrice și pentru ziua de mâine, probabilitatea ca peste 1% din "
        "clienții zonei să rămână fără curent în același timp, plus câți clienți ar fi afectați dacă se întâmplă "
        "(P10/P50/P90). Agentul folosește estimarea ca să trimită echipe din timp (`preposition_crew`) sau, când nu e sigur, "
        "să lase decizia dispecerului (`human_review`)."),
        "",
        "",
        "## De ce contează pentru PPC",
        "",
        ("- Întreruperile și compensațiile automate sunt pe lista problemelor neacoperite de cele 9 proiecte AI ale PPC "
        "(`memory/12-probleme-reale-ppc-2026.md`, problema D1)."),
        "- Rețele Electrice plătește circa 85% din compensațiile automate naționale (raportul ANRE pe 2024).",
        ("- Standardul ANRE (Ord. 46/2021, art. 15) cere restabilirea în 4/6/12 h pe vreme normală și în 48/72 h pe vreme "
        "deosebită; la depășire, fiecare client JT primește automat 30 lei. O echipă aflată deja în zonă scurtează "
        "restabilirea exact în zilele în care rețeaua e cea mai solicitată."),
        ("- PPC are din noiembrie 2025 un sistem nou de gestionare a echipelor de teren (WFM). Modelul îi dă ce-i lipsește: "
        "unde și când vor fi avarii mâine, cu cât de sigur e."),
        "",
        "- **Utilizatori:** dispecerii Rețele Electrice, prin planificator și interfață.",
        "- **Nu e pentru:** decizii automate fără om, despăgubiri, evaluarea clienților. Nu folosește date personale.",
        "",
        "## Date",
        "",
        ("- **Ținta:** EAGLE-I (ORNL), clienți fără curent pe comitat la 15 minute, CC BY 4.0, "
        "https://doi.org/10.6084/m9.figshare.24237376.v4."),
        (f"- **Eșantion:** {ti['counties']} comitate din {len(ti['states'])} state SUA ({', '.join(ti['states'])}), "
        f"ani de antrenare {', '.join(map(str, ti['years']))}, cu {ro_int(ti['rows'])} zile-comitat și {ro_int(ti['events'])} "
        "de evenimente."),
        ("- **Vremea:** Open-Meteo Historical Weather API (best_match: ERA5, ERA5-Land, ECMWF IFS), 10 variabile zilnice pe "
        "centroidul comitatului. Aceeași sursă e folosită în România (arhiva pentru zile trecute, prognoza pentru mâine)."),
        ("- **Curățare:** acoperire EAGLE-I sub 50% din zile pe comitat-an, valori blocate, vârfuri peste numărul de clienți, "
        "valori meteo imposibile. Detalii în `docs/data/B.md`."),
    ]
    if summ:
        lines += [
            (f"- **Ce a scos curățarea:** {summ.get('dropped_low_coverage_county_years', 0)} comitat-ani cu acoperire slabă, "
            f"{summ.get('dropped_stuck_days', 0)} zile cu valori blocate, {summ.get('clipped_over_100pct', 0)} vârfuri "
            "tăiate la 100%."),
        ]
    lines += [
        ("- **Date sintetice:** niciuna în antrenare și în test (`synthetic_share` = "
        f"{m['synthetic_share']})."),
        "",
        "## Modelul",
        "",
        ("- **Pasul 1:** LightGBM pentru P(vârf ≥ 1% din clienți), cu constrângeri monotone pe vânt, ploaie, zăpadă și "
        "polei (riscul nu scade când vremea se înrăutățește). Calibrare izotonică pe scoruri out-of-fold, cu fold-uri pe "
        "săptămâni."),
        ("- **Pasul 2:** LightGBM quantile (P10, P50, P90) pentru vârful procentual în zilele cu eveniment. Intervalul e lărgit "
        f"prin calibrare conformală (CQR), cu {num(model.cqr_offset)} pe scara log."),
        "- **Features:** " + ", ".join(f"`{f}`" for f, _ in FEATURE_SPEC) + ".",
        (f"- **Pragul de decizie:** {num(model.decision_threshold, 2)}, cel mai bun F1 pe scorurile out-of-fold din anii "
        "de antrenare. Planificatorul decide final, după valoare și echipele disponibile."),
        "",
        "## Evaluare (test separat)",
        "",
        f"Testul: {m['split']}. {ro_int(m['test_size'])} zile-comitat; prevalența evenimentului e {pct(mm['prevalence'])}.",
        "",
        "| Metrică | Model | Climatologie comitat × lună | Climatologie pe lună | Regula pe rafală |",
        "|---|---|---|---|---|",
        (f"| PR-AUC (principala) | **{num(mm['pr_auc'])}** | {num(bm['pr_auc'])} | {num(main['clim_month']['pr_auc'])} | "
        f"{num(main['gust_rule']['pr_auc'])} |"),
        (f"| ROC-AUC | {num(mm['roc_auc'])} | {num(bm['roc_auc'])} | {num(main['clim_month']['roc_auc'])} | "
        f"{num(main['gust_rule']['roc_auc'])} |"),
        (f"| Brier (mai mic e mai bine) | {num(mm['brier'], 4)} | {num(bm['brier'], 4)} | "
        f"{num(main['clim_month']['brier'], 4)} | {num(main['gust_rule']['brier'], 4)} |"),
        (f"| Recall evenimente severe (≥ 5%) la prag | {pct(mm['recall_severe_at_thr'])} | "
        f"{pct(bm['recall_severe_at_thr'])} | {pct(main['clim_month']['recall_severe_at_thr'])} | "
        f"{pct(main['gust_rule']['recall_severe_at_thr'])} |"),
        (f"| Recall evenimente extreme (≥ 10%) la prag | {pct(mm['recall_extreme_at_thr'])} | "
        f"{pct(bm['recall_extreme_at_thr'])} | {pct(main['clim_month']['recall_extreme_at_thr'])} | "
        f"{pct(main['gust_rule']['recall_extreme_at_thr'])} |"),
        "",
        (f"- **Cuantile** (zilele cu eveniment din test): acoperirea P10-P90 e {pct(mm['coverage_p10_p90'])} (ținta 80%; "
        f"fără calibrarea conformală: {pct(main['model'].get('coverage_p10_p90_without_conformal', float('nan')))}). "
        f"Pierderea pinball medie (scara log): model {num(mm['pinball_mean'])}, climatologia pe lună "
        f"{num(main['clim_month'].get('pinball_mean', float('nan')))}."),
    ]
    if lo:
        lines += [
            (f"- **State nevăzute** (leave-one-state-out, {lo['states']} state, anul {2025}): PR-AUC mediu "
            f"{num(lo['model_pr_auc_mean'])}, față de climatologia pe lună {num(lo['clim_month_pr_auc_mean'])} și regula "
            f"pe rafală {num(lo['gust_rule_pr_auc_mean'])}. Modelul bate climatologia în {lo['states_model_beats_clim']} "
            f"din {lo['states']} state. E situația din România: zone fără istoric de avarii."),
        ]
    if cap:
        r = cap["results"]
        lines += [
            (f"- **Echipe puține** ({cap['k_crews_per_day']} echipe pe zi pentru {cap['zones']} zone, câte una în zonele "
            "cu scorul cel mai mare): acoperă din clienții afectați "
            f"{pct(r['model']['customers_covered_share'])} cu modelul, {pct(r['regula_rafala']['customers_covered_share'])} "
            f"cu regula pe rafală, {pct(r['climatologie_comitat_luna']['customers_covered_share'])} cu climatologia, "
            f"{pct(r['aleator']['customers_covered_share'])} la întâmplare și "
            f"{pct(r['oracol']['customers_covered_share'])} cu un oracol care știe viitorul."),
        ]
    lines += [
        ("- **Figuri:** `fig_pr_curves.png`, `fig_reliability.png`, `fig_shap_importance.png`; analiza erorilor în "
        "`error_analysis.md`; backtestul din România în `backtest_romania.md`."),
        "",
    ]
    bt_path = REPORTS / "B" / "backtest_summary.json"
    if bt_path.exists():
        bt = json.loads(bt_path.read_text(encoding="utf-8"))
        c1, c2, c3 = bt["banat_2025_07_07_08"], bt["slobozia_2025_07_17"], bt["dobrogea_2023_11_26"]
        lines += [
            "## Backtest în România: trei furtuni reale (`reports/B/backtest_romania.md`)",
            "",
            (f"- **Banat, 7-8 iulie 2025** (cod roșu ANM de vijelii): riscul mediu e {num(c1['p_banat'], 2)} în Banat, față de "
             f"{num(c1['p_rest'], 2)} în rest; echipă recomandată în {c1['crews_banat_zone_days']} zone-zi din Banat și în "
             f"{c1['crews_rest_zone_days']} din rest."),
            (f"- **Slobozia, 17 iulie 2025** (cod roșu): zona e pe locul {c2['rank']} din {c2['zones']} după risc"
             + (f", la egalitate cu {', '.join(c2['tied_with'])}" if c2.get("tied_with") else "")
             + f" (P = {num(c2['p'], 2)})."),
            (f"- **Dobrogea, 26 noiembrie 2023** (cod portocaliu de viscol): riscul mediu e {num(c3['p_dobrogea'], 2)} în "
             f"Dobrogea, față de {num(c3['p_rest'], 2)} în rest; {c3['crews_dobrogea']} din {c3['zones_dobrogea']} zone primesc echipă."),
            "- Fără istoricul de avarii Rețele Electrice, verificarea e calitativă: zonele lovite, ziua, ordinul de mărime.",
            "",
        ]
    if exps:
        lines += ["## Ce am încercat", "", "| Varianta | Ce | PR-AUC | Brier |", "|---|---|---|---|"]
        lines += [f"| {e['varianta']} | {e['ce']} | {num(e['pr_auc'])} | {num(e['brier'], 4)} |" for e in exps]
        lines += [""]
    lines += [
        "## Folosirea în România și limitele, spuse cinstit",
        "",
        ("- **Transfer:** modelul e învățat în SUA și aplicat pe 26 de zone Rețele Electrice. E validat pe date externe "
        "(an nevăzut, state nevăzute) și trebuie calibrat pe istoricul de avarii Rețele Electrice înainte de producție. "
        "Fiecare lucrare poartă nota asta."),
        ("- **Features normalizate:** procente, densitate și logaritmul clienților, nu valori absolute. Zonele mai mari decât "
        "orice comitat din antrenare (Bucureștiul) sunt semnalate și trimise la om."),
        ("- **Rafalele convective sunt subestimate** de arhive și de prognoze (pe 8 iulie 2025: 40-70 km/h în arhivă, față "
        "de 90-120 km/h măsurați). Modelul învață pe aceeași vreme netezită, deci ordonează bine zonele, dar intensitatea "
        "locală rămâne incertă."),
        ("- **Căldura contează în model:** în datele din SUA, zilele foarte calde aduc avarii (suprasarcină, furtuni de "
        "după-amiază). În România, zilele de caniculă primesc deci un risc moderat chiar fără vânt, iar explicația o spune."),
        ("- **Evenimentele fără semnal meteo** (defecte de echipament) sunt circa jumătate din evenimentele de 1% și nu pot fi "
        "prezise din vreme. De aici vine plafonul de PR-AUC."),
        "- **Clienții pe zonă** sunt o aproximare din populație. Clienții pe județ sunt oficiali (RER, 31.12.2024).",
        ("- **Testul folosește vremea reconstituită** (arhiva Open-Meteo), nu prognoza făcută cu o zi înainte. În exploatare, "
         "cu prognoza, performanța va fi ceva mai mică, deci cifrele de test sunt mai degrabă o limită de sus. Incertitudinea "
         "prognozei e tratată separat: ensemble (40 de membri ICON-EPS) pentru mâine, trei modele pentru zilele trecute."),
        "",
        "## Îmbunătățiri viitoare",
        "",
        ("- **Mai mulți ani de antrenare (2021-2022):** EAGLE-I 2021-2022 e deja descărcat, dar vremea pentru acești ani ar "
         "cere circa 4.200 de apeluri Open-Meteo, peste cota gratuită rămasă (10.000 pe zi, comună pentru tot laptopul). "
         "N-am adăugat-o, ca să nu schimbăm cifrele după ce le-a învățat echipa."),
        ("- **Calibrarea pe istoricul de avarii Rețele Electrice:** pasul obligatoriu înainte de producție (transfer din "
         "SUA, prag, cuantile)."),
        ("- **Evaluare pe prognoza din ziua de dinainte** (Historical Forecast / Previous Runs API), nu pe vremea "
         "reconstituită, ca cifrele să arate performanța din exploatare."),
        "- **Zăpada:** variabile pentru zăpada grea și umedă (experimentul `zapada_uda_viscol` n-a ajutat cu datele zilnice).",
        "",
        "## „Nu sunt sigur”: când trimite la om",
        "",
        "- lipsesc rafala sau ploaia pentru ziua țintă;",
        "- zona sau vremea iese din intervalul văzut la antrenare (cu o marjă de 10%);",
        ("- sursele meteo nu se pun de acord (trei modele de prognoză pentru zilele trecute, 40 de membri ICON-EPS pentru "
        "mâine), iar intervalul probabilității trece peste prag;"),
        "- dacă Open-Meteo nu răspunde, agentul folosește ultima prognoză salvată și o scrie în lucrare.",
        "",
        "## Responsabilitate",
        "",
        ("- **EU AI Act:** sistemele AI pentru infrastructură critică sunt cu risc ridicat. Omul rămâne în buclă: modelul "
        "recomandă, iar planificatorul și dispecerul decid. Fiecare decizie are `prediction_id` și `model_version` în "
        "jurnalul de audit."),
        "- **Date:** fără date personale. Datele sunt publice, cu licențe deschise, citate în `docs/data/B.md`.",
        "",
        "## Reproducere",
        "",
        "```bash",
        "make b-data b-weather b-dataset   # date (EAGLE-I ~4 GB, ~6.300 de apeluri Open-Meteo)",
        m["reproduce_cmd"] + "   # metricile din acest card",
        "uv run python -m cyberpunks.b_furtuna.experiments && uv run python -m cyberpunks.b_furtuna.error_analysis",
        "uv run python -m cyberpunks.b_furtuna.backtest && uv run python -m cyberpunks.b_furtuna.model_card",
        "```",
        "",
    ]
    text = "\n".join(lines)
    OUT.write_text(text, encoding="utf-8")
    print(f"-> {OUT}")
    return text


if __name__ == "__main__":
    run()
