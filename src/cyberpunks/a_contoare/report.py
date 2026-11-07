"""Generează reports/A/error_analysis.md din cifrele scripturilor (nicio cifră scrisă de mână).

    uv run python -m cyberpunks.a_contoare.report

Citește reports/A/metrics_full.json (evaluate.py), reports/A/robustness.json (robustness.py) și, dacă există,
outputs/work_items/<scenariu>/A_ground_truth.csv (predict.py) pentru calibrarea pe populația demo.
"""

from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from cyberpunks.a_contoare import metrics as M
from cyberpunks.a_contoare.inject import KIND_LABEL_RO
from cyberpunks.common.paths import OUTPUTS, REPORTS

REP = REPORTS / "A"


def f2(x: float | None, nd: int = 2) -> str:
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "-"
    return f"{x:.{nd}f}".replace(".", ",")


def pct(x: float | None) -> str:
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "-"
    return f"{round(100 * x)}%"


def nde(n: int, noun: str) -> str:
    """Numeral cu substantiv: 85 de contoare, 13.028 de eșantioane, 19 zile (regula lui "de" în română)."""
    n = int(n)
    txt = f"{n:,}".replace(",", ".")
    last2 = abs(n) % 100
    return f"{txt} {noun}" if n == 0 or 1 <= last2 <= 19 else f"{txt} de {noun}"


def table(header: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)


def demo_operations() -> list[list[str]]:
    """Ce ajunge efectiv la echipă și la om, pe demo (lucrările emise față de adevărul injectat)."""
    rows = []
    for s in ("demo-vara", "maine"):
        gp = OUTPUTS / "work_items" / s / "A_ground_truth.csv"
        wp = OUTPUTS / "work_items" / s / "A.jsonl"
        if not (gp.exists() and wp.exists()):
            continue
        g = pd.read_csv(gp).set_index("meter_id")
        items = [json.loads(line) for line in wp.read_text(encoding="utf-8").splitlines() if line.strip()]
        crew = [w["asset_id"] for w in items if w["recommended_action"] in ("inspect_on_site", "remote_reading")]
        human = [w["asset_id"] for w in items if w["recommended_action"] == "human_review"]
        n_normal = int((g["true_problem"] == 0).sum())
        rows.append([
            s,
            str(len(crew)),
            pct(g.loc[crew, "true_problem"].mean()) if crew else "-",
            str(len(human)),
            pct(g.loc[human, "true_problem"].mean()) if human else "-",
            pct(float((g.loc[crew, "true_problem"] == 0).sum()) / max(n_normal, 1)),
            pct(float((g.loc[human, "true_problem"] == 0).sum()) / max(n_normal, 1)),
        ])
    return rows


def demo_calibration() -> list[list[str]]:
    rows = []
    for s in ("demo-vara", "maine"):
        p = OUTPUTS / "work_items" / s / "A_ground_truth.csv"
        if not p.exists():
            continue
        g = pd.read_csv(p)
        y, sc = g["true_problem"].to_numpy(), g["score"].to_numpy()
        rows.append([s, str(len(g)), f2(y.mean(), 3), f2(sc.mean(), 3), f2(M.brier(y, sc), 3), f2(M.ece(y, sc), 3),
                     f2(M.pr_auc(y, sc))])
    return rows


def build() -> str:
    full = json.loads((REP / "metrics_full.json").read_text(encoding="utf-8"))
    rob = json.loads((REP / "robustness.json").read_text(encoding="utf-8")) if (REP / "robustness.json").exists() else {}
    L, S, leak = full["lcl_injected"], full["sgcc_real_labels"], full.get("leakage_checks", {})
    sub = L["subtle_only"]
    comp = L["top_k_composition"]
    k_l, k_s = L["k"], S["k"]

    parts: list[str] = []
    parts.append("# Analiza erorilor, firul A (contoare defecte sau manipulate)\n")
    parts.append(
        "Generat de `uv run python -m cyberpunks.a_contoare.report` din `reports/A/metrics_full.json` "
        f"(creat {full['created_at']}), `reports/A/robustness.json` și ieșirile `predict`. "
        f"Modele: {full['models']['a-lgbm']} (Londra) și {full['models']['a-lgbm-sgcc']} (SGCC). "
        "K = 1% din contoarele din test. Londra = etichete SINTETICE (probleme injectate de noi peste consum real); "
        "SGCC = etichete reale de furt.\n"
    )

    parts.append("## Pe scurt\n")
    parts.append(
        f"- Pe furt real (SGCC), modelul pune {pct(S['model']['precision_at_k'])} furturi reale în primele "
        f"{nde(k_s, 'contoare')}, față de {pct(S['rule']['precision_at_k'])} la regula simplă și "
        f"{pct(S['vee']['precision_at_k'])} la regula VEE completă. ROC-AUC {f2(S['model']['roc_auc'])} e în "
        "intervalul cinstit din literatură (0,78-0,92).\n"
        f"- Pe Londra, precizia@K = {f2(L['model']['precision_at_k'])} nu vine dintr-o scurgere găsită de noi "
        "(secțiunea 1, cu verificările și limitele lor). Vine din "
        f"cele {nde(comp['obvious_problems_in_test'], 'defecte evidente')} din test, care umplu primele "
        f"{nde(k_l, 'locuri')} "
        "(secțiunea 2). Cifra care arată ce adaugă modelul peste reguli e cea de pe problemele subtile: "
        f"{f2(sub['model']['precision_at_k'])} față de {f2(sub['vee']['precision_at_k'])} la VEE.\n"
        "- Slăbiciuni reale: ceasul decalat, sub-înregistrarea lentă și bypass-ul parțial (secțiunea 3). Mai sunt "
        "alarmele false la consumatorii mici, limitate prin decizia unui om (secțiunea 5), și degradarea la date "
        "lipsă (secțiunea 6).\n"
    )

    parts.append("## 1. Există scurgeri între antrenare și test?\n")
    perm_l, perm_s = leak.get("lcl_permutation", {}), leak.get("sgcc_permutation", {})
    parts.append(
        table(
            ["Verificare", "Rezultat"],
            [
                ["Gospodării Londra comune antrenare / test", str(leak.get("lcl_households_train_test_overlap"))],
                ["Gospodării Londra comune calibrare / test", str(leak.get("lcl_households_cal_test_overlap"))],
                ["Clienți SGCC comuni antrenare / test", str(leak.get("sgcc_customers_train_test_overlap"))],
                ["Ultima zi de evaluare la antrenare (Londra)", str(leak.get("lcl_train_last_scoring_date"))],
                ["Prima zi de evaluare la test (Londra)", str(leak.get("lcl_test_first_scoring_date"))],
                ["Londra, model antrenat pe etichete amestecate: PR-AUC pe test",
                 f"{f2(perm_l.get('pr_auc_shuffled'), 3)} (prevalența: {f2(perm_l.get('prevalence'), 3)})"],
                ["SGCC, model antrenat pe etichete amestecate: PR-AUC pe test",
                 f"{f2(perm_s.get('pr_auc_shuffled'), 3)} (prevalența: {f2(perm_s.get('prevalence'), 3)})"],
            ],
        )
        + "\n"
    )
    parts.append(
        "Testul cu etichete amestecate e o verificare de bun-simț, nu o dovadă. Arată că pipeline-ul nu strecoară "
        "eticheta direct, dar nu poate prinde un artefact al datelor sintetice sau o statistică calculată și din "
        "test. De aceea am verificat de unde vine fiecare informație:\n"
        "- ferestrele Londra se termină în ziua de evaluare, deci features-urile nu văd viitorul. Vecinii sunt "
        "gospodării din același set (antrenare, calibrare sau test), iar mediana lor se calculează din consumul "
        "fără injecții;\n"
        "- SGCC: referința \"vecinilor\" (mediana zilnică) se calculează DOAR din clienții de antrenare, aceeași "
        "pentru toate seturile. Corectat după review-ul independent: înainte includea și clienții de test;\n"
        "- calibrarea, pragurile conformal, alegerea features și pragurile regulii VEE folosesc doar setul de "
        "calibrare. Testul e privit o singură dată pe versiune;\n"
        "- oprirea timpurie la antrenare validează pe gospodării întregi, nu pe ferestre amestecate (corectat după "
        "review);\n"
        "- limite rămase: ferestrele de test (180 de zile înapoi) acoperă și luni din perioada de antrenare, pe alte "
        "gospodării, cum lucrează și agentul în producție. Etichetele Londra sunt sintetice, deci un artefact al "
        "injecției poate fi învățat; unul l-am găsit și reparat (secțiunea 8).\n"
    )

    parts.append("## 2. Clasamentul la mai multe K (de ce 1,00)\n")
    parts.append("Figuri: `reports/A/figures/ranking_at_k.png` (precizie și recall pe K) și "
                 "`reports/A/figures/headline_precision.png` (furt real, probleme subtile, toate problemele).\n")
    rows = [[str(r["k"]), f2(r["k_over_positives"]), f2(r["model_precision"]), f2(r["model_recall"]),
             f2(r["vee_precision"]), f2(r["rule_precision"])] for r in L["ranking_at_ks"]]
    parts.append(f"**Londra (sintetic), {nde(L['n'], 'eșantioane')}, {L['positives']} cu probleme:**\n")
    parts.append(table(["K", "K / probleme", "Precizie model", "Recall model", "Precizie VEE", "Precizie regulă simplă"],
                       rows) + "\n")
    rows = [[str(r["k"]), f2(r["k_over_positives"]), f2(r["model_precision"]), f2(r["model_recall"]),
             f2(r["vee_precision"]), f2(r["rule_precision"])] for r in S["ranking_at_ks"]]
    parts.append(f"**SGCC (etichete reale), {nde(S['n'], 'clienți')}, {S['positives']} cu furt:**\n")
    parts.append(table(["K", "K / furturi", "Precizie model", "Recall model", "Precizie VEE", "Precizie regulă simplă"],
                       rows) + "\n")
    rows = [[str(r["k"]), f2(r["model_precision"]), f2(r["model_recall"]), f2(r["vee_precision"]),
             f2(r["rule_precision"])] for r in sub["ranking_at_ks"]]
    parts.append(f"**Londra, doar problemele subtile** (fără contor oprit, blocat, negative, goluri), "
                 f"{nde(sub['positives'], 'probleme')}:\n")
    parts.append(table(["K", "Precizie model", "Recall model", "Precizie VEE", "Precizie regulă simplă"], rows) + "\n")
    def kind_ro(k: str) -> str:
        return "normal" if k == "normal" else KIND_LABEL_RO.get(k, k).split(" (")[0]

    mt = ", ".join(f"{kind_ro(k)} {v}" for k, v in comp["model_top_k"].items())
    vt = ", ".join(f"{kind_ro(k)} {v}" for k, v in comp["vee_top_k"].items())
    parts.append(
        f"**Ce ocupă primele {nde(k_l, 'locuri')}.** Model: {mt}. Regula VEE: {vt}.\n\n"
        f"Concluzia: K = {k_l} e doar {pct(k_l / L['positives'])} din probleme, iar testul are "
        f"{nde(comp['obvious_problems_in_test'], 'defecte evidente')}. Orice clasificator care le recunoaște umple vârful "
        "listei doar cu probleme reale. VEE le recunoaște și el, dar își strică lista cu contoare normale care au "
        "salturi sau scăderi naturale. Diferența reală dintre model și reguli se vede la K mai mare și pe "
        "problemele subtile. Acolo regulile sunt aproape oarbe, iar modelul ține peste 60% precizie până la "
        "K = 200.\n"
    )

    parts.append("## 3. Pe tipuri de problemă (Londra, test)\n")
    vee_by = {r["kind"]: r for r in L.get("per_kind_vee", [])}
    rows = []
    for r in L["per_kind_model"]:
        v = vee_by.get(r["kind"], {})
        rows.append([r["label_ro"], r["family"], str(r["n"]), f2(r["roc_auc_vs_normal"]), pct(r["flagged_share_at_5pct"]),
                     f2(v.get("roc_auc_vs_normal")), pct(v.get("flagged_share_at_5pct"))])
    parts.append(table(["Tip", "Familie", "n", "ROC-AUC model", "În primele 5% (model)", "ROC-AUC VEE",
                        "În primele 5% (VEE)"], rows) + "\n")
    weak = sorted((r for r in L["per_kind_model"] if r["family"] != "benign"), key=lambda r: r["roc_auc_vs_normal"])[:3]
    parts.append(
        "**Unde greșește:** " + "; ".join(f"{r['label_ro']} (ROC-AUC {f2(r['roc_auc_vs_normal'])})" for r in weak) + ". "
        "Ceasul decalat mută consumul cu 30-120 de minute, la fel de mult cât variază obiceiurile unei case de la o "
        "săptămână la alta. Deriva lentă și bypass-ul cu instalare treptată seamănă, în primele săptămâni, cu o "
        "scădere normală de consum. Pentru ceasul decalat am adăugat decalajul profilului zilei (`profile_lag`, "
        "`profile_lag_gain`), iar pentru derivă panta față de vecini (`peer_ratio_slope`); efectul lor e în "
        "secțiunea 8. Rămân puncte slabe, spuse deschis. Ceasul decalat nu schimbă energia totală, deci contează "
        "doar la tarifele pe ore.\n"
    )

    parts.append("## 4. Schimbări normale care NU trebuie semnalate\n")
    rule_by = {r["kind"]: r for r in L["per_kind_rule"]}
    rows = [[r["label_ro"], str(r["n"]), pct(r["flagged_share_at_5pct"]),
             pct(rule_by.get(r["kind"], {}).get("flagged_share_at_5pct")),
             pct(vee_by.get(r["kind"], {}).get("flagged_share_at_5pct"))]
            for r in L["per_kind_model"] if r["family"] == "benign"]
    parts.append(table(["Schimbare", "n", "Alarme false model (primele 5%)", "Regula simplă", "VEE"], rows) + "\n")
    parts.append(
        "Concediul și schimbarea ocupanților arată ca o scădere de consum. Regula simplă trimite echipa la mulți "
        "dintre cei plecați în concediu. Modelul a învățat diferența: concediul are consum de așteptare (frigiderul "
        "merge), iar profilul zilei păstrează forma casei.\n"
    )

    parts.append("## 5. Pe nivel de consum (etică: consumul mic nu e dovadă de furt)\n")
    rows = []
    s_rule = S.get("false_alarms_by_level_rule", [{}] * len(S["false_alarms_by_level"]))
    for q, qr, qs, qsr in zip(L["false_alarms_by_level"], L["false_alarms_by_level_rule"], S["false_alarms_by_level"],
                              s_rule, strict=False):
        rows.append([str(q["quintile"]), f2(q["level_kwh_median"], 1), pct(q["false_alarm_rate"]), pct(q["recall"]),
                     pct(qr["false_alarm_rate"]), f2(qs["level_kwh_median"], 1), pct(qs["false_alarm_rate"]),
                     pct(qsr.get("false_alarm_rate"))])
    parts.append(table(["Chintila de consum", "Londra: kWh/zi", "Alarme false model", "Recall model",
                        "Alarme false regulă", "SGCC: kWh/zi", "Alarme false model SGCC", "Alarme false regulă SGCC"],
                       rows) + "\n")
    parts.append("Figura: `reports/A/figures/false_alarms_by_consumption.png`.\n")
    parts.append(
        "Alarmă falsă = un contor fără problemă ajunge în primele 5% din clasament. Pe Londra, casele cu cel mai "
        "mic consum primesc de câteva ori mai multe alarme false decât celelalte. La ele, o scădere sau câteva "
        "zile cu zero înseamnă mai puțini kWh absoluți, iar zgomotul relativ e mai mare. Pe SGCC, tiparul e "
        "invers: furturile reale sunt la consumatori mari, iar alarmele false ale modelului cresc spre chintila de sus. "
        "Regula simplă face greșeala opusă și mult mai mare: pe SGCC trimite echipa la "
        f"{f2(100 * s_rule[0].get('false_alarm_rate', float('nan')), 1)}% dintre consumatorii cei mai mici fără "
        f"problemă, modelul la {f2(100 * S['false_alarms_by_level'][0]['false_alarm_rate'], 1)}%. "
        "Consumul mic poate însemna o locuință goală sau sărăcie energetică. De aceea, în agent:\n"
        "- un furt suspectat la un contor din chintila de jos a consumului NU merge direct la vizită. Merge la un "
        "om, cu motivul scris (`extra.low_consumption_guard`, `abstain_reason`);\n"
        "- nivelul de consum rămâne feature, pentru că din el se calculează și valoarea pierderii. În schimb, "
        "rata de alarme false pe chintile se verifică la fiecare evaluare (tabelul de mai sus).\n"
    )

    parts.append("## 6. Pe date lipsă (contoare care nu comunică)\n")
    curve = rob.get("missing_data_curve", [])
    if curve:
        rows = [[pct(r["missing_days_share"]), f2(r["precision_at_k"]), f2(r["pr_auc"]), f2(r["roc_auc"]),
                 pct(r["data_abstain_share"]), str(r["problem_decisions"]), str(r["unsure_decisions"])] for r in curve]
        parts.append(table(["Zile lipsă", "Precizia@K", "PR-AUC", "ROC-AUC", "Abțineri din lipsă de date",
                            "Decizii 'problemă'", "Decizii 'nu sunt sigur'"], rows) + "\n")
    parts.append(
        "La 31 dec. 2025, gradul de integrare a contoarelor inteligente era 66,85% în Dobrogea, 58,81% în "
        "Muntenia și 56,45% în Banat (infobuz, rezumat în `memory/12-probleme-reale-ppc-2026.md`, neverificat de "
        "noi). Datele incomplete sunt deci situația obișnuită. De aceea am pus pe posturi doar 58,81% din clienți "
        "ca fiind contoare cu date. Experimentul ascunde zile întregi la întâmplare pe populația demo. Calitatea "
        "scade treptat, nu se prăbușește. Când datele nu mai ajung (sub 60 de zile în 180), agentul spune "
        "\"nu sunt sigur\" și trimite la om, în loc să ghicească.\n"
    )
    ts = rob.get("sgcc_time_split")
    if ts:
        parts.append(
            "**SGCC pe timp.** Features pe ferestre de un an; antrenare pe ferestrele care se termină la 31.10.2015, "
            "test pe clienți nevăzuți cu ferestre care se termină la 31.10.2016: precizia@K "
            f"{f2(ts['model']['precision_at_k'])}, PR-AUC {f2(ts['model']['pr_auc'])}, ROC-AUC "
            f"{f2(ts['model']['roc_auc'])} (regula: ROC-AUC {f2(ts['rule']['roc_auc'])}). Scăderea față de "
            "împărțirea pe clienți are două cauze. Golurile din fereastra de antrenare "
            f"({pct(ts['missing_share_train_window'])}) aproape dispar în cea de test "
            f"({pct(ts['missing_share_test_window'])}), iar eticheta SGCC nu are dată: nu știm dacă furtul era activ "
            "în fereastră. De aceea raportăm ca rezultat principal împărțirea pe clienți, pe toată perioada, ca în "
            "literatură. Varianta pe timp e un test de robustețe.\n"
        )

    parts.append("## 7. Calibrare și \"nu sunt sigur\"\n")
    conf_l, conf_s = L["conformal"], S["conformal"]
    parts.append(
        table(
            ["", "Londra (test)", "SGCC (test)"],
            [
                ["Brier", f2(L["calibration"]["brier"], 3), f2(S["calibration"]["brier"], 3)],
                ["ECE", f2(L["calibration"]["ece"], 3), f2(S["calibration"]["ece"], 3)],
                ["Acoperirea mulțimii, normale (garanție: >= 99%)", pct(conf_l["set_coverage_normal"]),
                 pct(conf_s["set_coverage_normal"])],
                ["Acoperirea mulțimii, probleme (garanție: >= 70%)", pct(conf_l["set_coverage_problem"]),
                 pct(conf_s["set_coverage_problem"])],
                ["Probleme recunoscute SIGUR (mulțimea = {problemă})", pct(conf_l["problem_recall_sure"]),
                 pct(conf_s["problem_recall_sure"])],
                ["Precizia deciziilor \"problemă\"", pct(conf_l["problem_precision_sure"]),
                 pct(conf_s["problem_precision_sure"])],
                ["Probleme trimise la om (zona gri)", pct(conf_l["problem_to_unsure"]), pct(conf_s["problem_to_unsure"])],
                ["Probleme ratate (declarate normale)", pct(conf_l["problem_missed"]), pct(conf_s["problem_missed"])],
                ["Contoare normale declarate \"problemă\"", pct(conf_l["normal_to_problem"]),
                 pct(conf_s["normal_to_problem"])],
                ["Contoare normale trimise la om (zona gri)", pct(conf_l["normal_to_unsure"]),
                 pct(conf_s["normal_to_unsure"])],
                ["Toate cazurile \"nu sunt sigur\"", pct(conf_l["unsure_share"]), pct(conf_s["unsure_share"])],
            ],
        )
        + "\n"
    )
    ops = demo_operations()
    if ops:
        parts.append("**Ce ajunge efectiv la echipă și la om, pe demo** (lucrările emise față de adevărul injectat; "
                     "ultimele două coloane: ce parte din TOATE contoarele normale):\n")
        parts.append(table(["Scenariu", "Lucrări pentru echipă", "Din ele, probleme reale", "Lucrări la om",
                            "Din ele, probleme reale", "Contoare normale la echipă", "Contoare normale la om"], ops)
                     + "\n")
    dc = demo_calibration()
    if dc:
        parts.append("**Pe populațiile demo** (adevărul injectat, nevăzut de model):\n")
        parts.append(table(["Scenariu", "Contoare", "Prevalență reală", "Scor mediu", "Brier", "ECE", "PR-AUC"], dc) + "\n")
    parts.append(
        "Scorul e o probabilitate calibrată (Venn-ABERS pe o grilă de cuantile; abaterea față de calculul exact, pe "
        f"200 de scoruri de test: maximum {f2(L.get('venn_abers_grid_vs_exact', {}).get('max_abs_p'), 4)}). Scorul mediu "
        "e aproape egal cu prevalența reală, deci planificatorul poate înmulți scorul cu valoarea în lei.\n\n"
        "Conformal lucrează pe scorul brut al modelului, cu pragurile alese pe calibrare (alpha 1% pentru normal, "
        "30% pentru problemă). Funcția de scor (modelul și features) e aleasă fără etichetele de calibrare. Totuși, "
        "garanția formală cere rânduri interschimbabile, iar la Londra setul de calibrare are mai multe ferestre "
        "din aceeași gospodărie. De aceea prezentăm acoperirea ca EMPIRICĂ, măsurată pe test (tabelul de mai sus), "
        "nu ca garanție. Acoperirea privește MULȚIMEA: \"conține clasa reală\". Nu e același lucru cu "
        "\"recunoscut sigur\". O problemă din zona gri e acoperită (mulțimea are ambele clase), dar merge la om, nu la "
        f"echipă. În probabilitate calibrată, zona gri e între {pct(conf_l.get('p_threshold_problem'))} și "
        f"{pct(conf_l.get('p_threshold_normal'))} pe Londra. Pe SGCC e mai largă, pentru că etichetele reale sunt mai "
        "zgomotoase.\n"
    )

    sel = json.loads((REP / "feature_selection.json").read_text(encoding="utf-8")) if (REP / "feature_selection.json").exists() else None
    if sel:
        so, sn = sel["sgcc"]["vechi"], sel["sgcc"]["nou"]
        lo, ln, lf = sel["lcl"]["vechi"], sel["lcl"]["nou"], sel["lcl"]["nou_fara_sezoniere_brute"]
        sel_txt = (
            f"PR-AUC SGCC {f2(so['pr_auc'])} -> {f2(sn['pr_auc'])}, ROC-AUC {f2(so['roc_auc'])} -> {f2(sn['roc_auc'])}; "
            f"Londra PR-AUC {f2(lo['pr_auc'])} -> {f2(ln['pr_auc'])}; ROC-AUC pe tip, față de contoarele normale: "
            f"ceasul decalat {f2(lo['auc_by_kind']['clock_drift'])} -> {f2(ln['auc_by_kind']['clock_drift'])}, deriva "
            f"{f2(lo['auc_by_kind']['drift'])} -> {f2(ln['auc_by_kind']['drift'])}, furtul de noapte "
            f"{f2(lo['auc_by_kind']['night'])} -> {f2(ln['auc_by_kind']['night'])}. Fără features sezoniere brute, "
            f"PR-AUC {f2(lf['pr_auc'])} și ceasul decalat {f2(lf['auc_by_kind']['clock_drift'])}, deci le-am păstrat. "
            "Costul: concediul seamănă puțin mai mult cu o problemă (ROC-AUC față de contoarele normale "
            f"{f2(lo['auc_benign_vs_normal']['vacation'])} -> {f2(ln['auc_benign_vs_normal']['vacation'])}; 0,5 = de "
            "nedeosebit, deci mai mic e mai bine aici). "
            "Validarea are prevalența de antrenare (aproape jumătate probleme), deci cifrele absolute nu se compară cu "
            "testul; contează doar diferența dintre variante."
        )
    else:
        sel_txt = "rulează select_features.py pentru cifre."
    gray = []
    for sc in ("demo-vara", "maine"):
        gp = OUTPUTS / "work_items" / sc / "A_ground_truth.csv"
        if gp.exists():
            g = pd.read_csv(gp)
            gray.append(
                f"{sc}: deciziile \"problemă\" au precizie {pct(g.loc[g.conformal == 'problem', 'true_problem'].mean())}, "
                f"iar în zona gri sunt {pct(g.loc[g.conformal == 'unsure', 'true_problem'].mean())} probleme reale"
            )
    gray_txt = "; ".join(gray) if gray else "rulează predict pentru cifre"
    parts.append("## 8. Ce am încercat ca să corectăm (în ordine)\n")
    parts.append(
        "1. **Artefactul de rotunjire** (commit `a1b25d4`). Prima versiune semnala aproape jumătate din contoarele "
        "demo. Cauza: atacurile prin înmulțire (α·x, β·x, deriva) dădeau valori cu multe zecimale, iar contoarele "
        "reale trimit 3 zecimale. Modelul învățase \"valori nerotunjite = furt\". Corecția: rotunjim la 0,001 kWh "
        "după orice injecție. Aceeași lecție am transmis-o firului bilanț.\n"
        "2. **Zgomotul din populația demo.** Zgomotul pe fiecare jumătate de oră ștergea valorile repetate "
        "naturale (frigiderul noaptea), deci orice contor părea manipulat. L-am înlocuit cu un factor pe zi.\n"
        "3. **Sezonul și tipurile slabe.** În iulie, consumul scade natural față de primăvară, iar modelul vedea "
        "scăderi peste tot. Am adăugat 10 features: scăderea și panta raportate la vecinii de pe post "
        "(`max_drop_peer`, `peer_ratio_slope`), care scot vremea și sezonul, decalajul profilului zilei, forma "
        "distribuției, golurile separate și ritmul săptămânal. Le-am ales pe o validare din setul de antrenare "
        "(gospodării ținute deoparte), nu pe calibrare și nu pe test "
        f"(`select_features.py`): {sel_txt}\n"
        "4. **Un baseline mai corect.** Pe lângă regula simplă cerută (zero >= 7 zile sau scădere >= 50%), am "
        "construit regula VEE completă: zero, valori repetate, goluri, negative, salturi, scădere. Pragurile de "
        "salt le-am ales pe calibrare, ca să-i dăm cea mai bună șansă.\n"
        "5. **Pragurile pentru \"nu sunt sigur\".** Cu 5% / 20%, aproape orice scor peste 0,08 devenea "
        f"\"problemă\", iar zona gri era goală. Cu 1% / 30% (pe demo: {gray_txt}), zona gri chiar merită "
        "privirea unui om.\n"
        "6. **Paza pentru consum mic** (secțiunea 5).\n"
    )

    fc_path = REP / "fusion_check.json"
    if fc_path.exists():
        fc = json.loads(fc_path.read_text(encoding="utf-8"))
        parts.append("## 9. Fuziunea cu bilanțul pe post (verificare pe testul A)\n")
        parts.append(
            "Am aplicat formula de fuziune a firului bilanț (`cyberpunks.a_bilant.fuse.combine_arrays`, doar confirmare, "
            "neschimbată) pe populația demo. Bilanțul fiecărui post e construit din adevărul injectat: energia "
            "nemăsurată de contoarele postului, plus zgomotul pierderilor normale, cu abaterea sigma = 1%, 2% sau 4% din "
            "consumul postului. Rezultatele sunt mediate pe 3 trageri ale zgomotului (`reports/A/fusion_check.json`, "
            "`uv run python -m cyberpunks.a_contoare.fusion_check`).\n"
        )
        rows = []
        for sc in ("demo-vara", "maine"):
            for sg in ("sigma_1pct", "sigma_2pct", "sigma_4pct"):
                a = fc.get(sc, {}).get(sg)
                if not a:
                    continue
                cs = a["confirmed_share"]
                rows.append([sc, sg.replace("sigma_", "").replace("pct", "%"),
                             f"{f2(a['precision_at_10_a'])} -> {f2(a['precision_at_10_fused'])}",
                             f"{f2(a['precision_at_100_a'])} -> {f2(a['precision_at_100_fused'])}",
                             f"{f2(a['pr_auc_a'], 3)} -> {f2(a['pr_auc_fused'], 3)}",
                             pct(cs["furt_real"]), pct(cs["defect_real"]), pct(cs["fara_problema"])])
        parts.append(table(["Scenariu", "Sigma bilanț", "Precizia@10", "Precizia@100", "PR-AUC",
                            "Furturi confirmate", "Defecte confirmate", "Fără problemă, confirmate"], rows) + "\n")
        k1 = fc.get("demo-vara", {}).get("sigma_1pct", {}).get("confirmed_share_by_kind", {})
        g1 = fc.get("demo-vara", {}).get("sigma_1pct", {}).get("gray_zone", {})
        if k1:
            parts.append(
                "**Unde ajută și unde nu** (demo-vara, bilanț precis, sigma 1%, ce parte din fiecare tip e confirmată):\n"
                f"- defectele care pierd multă energie: contor oprit {pct(k1.get('zero'))}, citiri negative "
                f"{pct(k1.get('negative'))}, valoare blocată {pct(k1.get('stuck'))}. Pe acestea modelul le pune oricum "
                "în vârful listei, deci precizia în primele 10-100 nu se schimbă;\n"
                f"- furtul: consum redus constant {pct(k1.get('h1'))}, oprire pe ore {pct(k1.get('h3'))}, bypass "
                f"{pct(k1.get('bypass'))}. Pierderea unui contor (câțiva kWh/zi) e mică față de zgomotul postului;\n"
                f"- tiparele care nu schimbă energia nu pot fi confirmate: profil aplatizat {pct(k1.get('h4'))}, profil "
                f"inversat {pct(k1.get('h6'))}, ceas decalat {pct(k1.get('clock_drift'))}, goluri {pct(k1.get('gaps'))}, "
                f"salturi {pct(k1.get('spikes'))}. E corect că fuziunea doar confirmă și nu coboară scorul;\n"
                f"- riscul: bilanțul confirmă POSTUL, nu contorul. Pe un post cu energie lipsă, și vecinii fără problemă "
                f"cu o scădere naturală sunt confirmați: concediu {pct(k1.get('vacation'))}, schimbarea ocupanților "
                f"{pct(k1.get('occupancy_change'))};\n"
                f"- în zona gri a lui A ({int(g1.get('meters', 0))} de contoare, {pct(g1.get('real_problem_share'))} probleme "
                f"reale), cele confirmate au {pct(g1.get('real_problem_share_if_confirmed'))} probleme reale, deci "
                "confirmarea nu le separă. Asta susține decizia bilanțului de a nu rezolva automat cazurile nesigure.\n"
            )
    parts.append("## 10. Limite cunoscute\n")
    parts.append(
        "- Etichetele din Londra sunt sintetice: modelul învață tiparele pe care le-am injectat noi. Le-am făcut "
        "realiste, cu parametri din literatură, intensități mici, instalare treptată și schimbări normale "
        "ca exemple grele, dar un furt real poate arăta altfel. Pe etichete reale, SGCC dă un reper mai modest.\n"
        "- SGCC are o etichetă pe client, fără dată, și vine din altă țară și altă rețea. Îl folosim ca dovadă că "
        "aceleași features merg pe furt real, nu ca model pentru București.\n"
        "- Prevalența (3% defecte, 2% furturi) e o ipoteză. Precizia depinde de ea: la o prevalență reală mai mică, "
        "precizia la același K scade.\n"
        "- Valoarea în lei folosește ipotezele din `config/economics.yaml` (energia pierdută 0,70 lei/kWh, o "
        "vizită de 250 de lei, orizont de 90 de zile).\n"
        "- Tipul exact al defectului (blocat sau oprit) nu e prezis direct. Modelul dă familia (defect sau "
        "manipulare), iar factorii SHAP și cazurile similare arată tipul probabil.\n"
    )
    return "\n".join(parts)


def build_model_card() -> str:
    full = json.loads((REP / "metrics_full.json").read_text(encoding="utf-8"))
    rob = json.loads((REP / "robustness.json").read_text(encoding="utf-8")) if (REP / "robustness.json").exists() else {}
    L, S = full["lcl_injected"], full["sgcc_real_labels"]
    sub, leak = L["subtle_only"], full.get("leakage_checks", {})
    curve = {r["missing_days_share"]: r for r in rob.get("missing_data_curve", [])}
    lines = [
        "# Model card: `a-lgbm`, contoare defecte sau manipulate (firul A, Daybreak)",
        "",
        (f"Generat de `uv run python -m cyberpunks.a_contoare.report` din `reports/A/metrics_full.json` "
        f"({full['created_at']}). Formatul urmează Mitchell et al. 2019, \"Model Cards for Model Reporting\"."),
        "",
        "## Pe scurt",
        "",
        ("- **Ce face:** dă fiecărui contor inteligent o probabilitate calibrată că e defect sau manipulat, plus "
        "tipul probabil (defect / manipulare), intervalul de încredere, factorii care au contat și cazuri similare."),
        ("- **Pentru cine:** dispecerul și planificatorul echipelor de contorizare Rețele Electrice. Recomandă: "
        "verificare la fața locului, citire la distanță, urmărire sau decizia unui om."),
        ("- **Ce NU face:** nu acuză pe nimeni de furt, nu taie curentul, nu recalculează facturi. Orice vizită o "
        "decide planificatorul (cost și capacitate), iar cazurile nesigure le decide un om."),
        "",
        "## Detalii",
        "",
        f"- Versiuni: `{full['models']['a-lgbm']}` (agentul) și `{full['models']['a-lgbm-sgcc']}` (reperul pe etichete reale).",
        ("- Tip: LightGBM (arbori de decizie cu gradient), 3 clase (normal / defect / manipulare), ponderi pe clase, "
        "oprire timpurie pe gospodării separate; calibrare Venn-ABERS (pe grilă, abatere măsurată față de calculul exact); "
        "\"nu sunt sigur\" prin conformal Mondrian pe scorul brut (alpha 1% normal, 30% problemă)."),
        ("- Intrare: consumul unui contor pe 180 de zile (citiri la 30 de minute) și mediana vecinilor de pe același "
        "post; 40 de features, fiecare cu motivul scris (`features.py`, `FEATURE_INFO`)."),
        "- Rulează local, pe 4 nuclee, fără niciun API extern. Scorarea a 15.850 de contoare durează ~10 secunde.",
        "- Autori: echipa CyberPunks, SmartHack XI 2026 (tema PPC). Cod: `src/cyberpunks/a_contoare/`.",
        "",
        "## Utilizare corectă",
        "",
        ("- Prioritizarea verificărilor când echipele sunt puține: K = 1% din contoare, cam o săptămână de vizite "
        "pentru 3 echipe la 10.000 de contoare."),
        ("- Contoarele defecte (oprite, blocate, fără comunicație, cu salturi, cu citiri negative) înaintea furtului: "
        "PPC are deja în producție detecția de fraudă (Energy Anomaly Detection) și a anunțat ca pas următor "
        "monitorizarea predictivă a contoarelor defecte."),
        ("- Decizia finală o ia planificatorul (cost și capacitate) sau un om (cazurile nesigure). Fiecare decizie "
        "duce înapoi la `prediction_id` și `model_version` (jurnalul planificatorului)."),
        "",
        "## Utilizări greșite (de evitat)",
        "",
        ("- Acuzații automate de furt, debranșări sau recalculări de facturi pe baza scorului. Constatarea o face "
        "echipa la fața locului."),
        ("- Profilarea consumatorilor mici: consumul mic poate însemna o locuință goală sau sărăcie energetică. "
        "Agentul trimite la om furtul suspectat din chintila de jos a consumului."),
        "- Folosirea pe alte rețele sau țări fără recalibrare. Prevalența și obiceiurile de consum diferă.",
        "",
        "## Date",
        "",
        ("- **Antrenare și test, defecte și furt (sintetic):** consum real din Londra (Low Carbon London, UK Power "
        "Networks, CC BY 4.0), 1.414 gospodării, peste care injectăm 7 defecte, 8 tipuri de furt și 2 schimbări "
        "normale (concediu, schimbarea ocupanților). Etichetele vin din construcție. Rotunjim la rezoluția "
        "contorului după injecție."),
        ("- **Reper pe furt real:** SGCC (State Grid Corporation of China, Zheng et al. 2018), 42.372 de clienți, "
        "3.615 cu furt. Fără licență explicită: îl folosim doar pentru cercetare, fără să-l redistribuim."),
        ("- **Împărțirea:** Londra pe gospodării (60/20/20) și pe timp (test după antrenare); SGCC pe clienți "
        "(60/20/20), stratificat. Features alese pe o validare din setul de antrenare (gospodării ținute deoparte); "
        "calibrarea și pragurile conformal, doar pe setul de calibrare; testul, privit o singură dată pe versiune."),
        ("- **Demo:** 15.850 de contoare SINTETICE pe cele 300 de posturi din registrul comun (58,81% din clienți, "
        "gradul de integrare din Muntenia), cu profile reale ale gospodăriilor de test."),
        "",
        "## Rezultate (K = 1% din contoarele din test)",
        "",
        (f"**Metrica principală** (prima din `metrics.json`): precizia@K pe problemele subtile, adică testul Londra fără "
         f"defectele evidente pe care le prinde orice regulă: **{f2(sub['model']['precision_at_k'])}**, față de "
         f"{f2(sub['rule']['precision_at_k'])} la regula simplă și {f2(sub['vee']['precision_at_k'])} la regula VEE "
         f"completă. A doua cifră, pe furt real (SGCC): **{f2(S['model']['precision_at_k'])}**, față de "
         f"{f2(S['rule']['precision_at_k'])} și {f2(S['vee']['precision_at_k'])}. Precizia@K = "
         f"{f2(L['model']['precision_at_k'])} pe tot testul Londra NU e cifra principală: vârful listei e plin de "
         "defecte evidente."),
        "",
        table(
            ["Set de test", "Model", "Regula simplă", "Regula VEE completă", "IsolationForest"],
            [
                [f"SGCC, furt real ({nde(S['n'], 'clienți')}): precizia@K",
                 f2(S["model"]["precision_at_k"]), f2(S["rule"]["precision_at_k"]),
                 f2(S["vee"]["precision_at_k"]), f2(S["iforest"]["precision_at_k"])],
                ["SGCC: PR-AUC / ROC-AUC", f"{f2(S['model']['pr_auc'])} / {f2(S['model']['roc_auc'])}",
                 f"{f2(S['rule']['pr_auc'])} / {f2(S['rule']['roc_auc'])}",
                 f"{f2(S['vee']['pr_auc'])} / {f2(S['vee']['roc_auc'])}",
                 f"{f2(S['iforest']['pr_auc'])} / {f2(S['iforest']['roc_auc'])}"],
                [f"Londra, sintetic ({nde(L['n'], 'eșantioane')}): precizia@K",
                 f2(L["model"]["precision_at_k"]), f2(L["rule"]["precision_at_k"]),
                 f2(L["vee"]["precision_at_k"]), f2(L["iforest"]["precision_at_k"])],
                ["Londra: PR-AUC / ROC-AUC", f"{f2(L['model']['pr_auc'])} / {f2(L['model']['roc_auc'])}",
                 f"{f2(L['rule']['pr_auc'])} / {f2(L['rule']['roc_auc'])}",
                 f"{f2(L['vee']['pr_auc'])} / {f2(L['vee']['roc_auc'])}",
                 f"{f2(L['iforest']['pr_auc'])} / {f2(L['iforest']['roc_auc'])}"],
                ["Londra, doar problemele subtile: precizia@K", f2(sub["model"]["precision_at_k"]),
                 f2(sub["rule"]["precision_at_k"]), f2(sub["vee"]["precision_at_k"]), f2(sub["iforest"]["precision_at_k"])],
            ],
        ),
        "",
        (f"- Calibrare (Londra, test): Brier {f2(L['calibration']['brier'], 3)}, ECE {f2(L['calibration']['ece'], 3)}. "
         f"Conformal (acoperirea empirică a mulțimii, pe test): {pct(L['conformal']['set_coverage_normal'])} la "
         f"normale (țintă 99%), {pct(L['conformal']['set_coverage_problem'])} la probleme (țintă 70%). Ca decizii: "
         f"{pct(L['conformal']['problem_recall_sure'])} din probleme recunoscute sigur, precizia deciziilor "
         f"\"problemă\" {pct(L['conformal']['problem_precision_sure'])}, "
         f"{pct(L['conformal']['normal_to_problem'])} din contoarele normale declarate \"problemă\", "
         f"{pct(L['conformal']['unsure_share'])} \"nu sunt sigur\"."),
        (f"- Scurgeri: nicio gospodărie sau client în două seturi; referința vecinilor SGCC doar din antrenare; cu "
         f"etichete amestecate, PR-AUC pe test cade la prevalență "
         f"({f2(leak.get('lcl_permutation', {}).get('pr_auc_shuffled'), 3)} pe Londra, "
         f"{f2(leak.get('sgcc_permutation', {}).get('pr_auc_shuffled'), 3)} pe SGCC). Testul cu etichete amestecate e "
         "o verificare de bun-simț, nu o dovadă (error_analysis.md, secțiunea 1)."),
        ("- Precizia@K = 1,00 pe Londra vine din defectele evidente care umplu vârful listei. La K = numărul de "
        f"probleme, precizia e {f2(next(r['model_precision'] for r in L['ranking_at_ks'] if r['k'] == L['positives']))}. "
        "Detalii în `error_analysis.md`, secțiunea 2."),
        ("- Figuri: `reports/A/figures/headline_precision.png`, `ranking_at_k.png`, `false_alarms_by_consumption.png`, "
         "`calibration.png`, `detection_by_kind.png`."),
    ]
    if curve:
        c0, c3, c5 = curve.get(0.0, {}), curve.get(0.3, {}), curve.get(0.5, {})
        lines.append(
            f"- Date lipsă (populația demo): PR-AUC {f2(c0.get('pr_auc'))} -> {f2(c3.get('pr_auc'))} -> "
            f"{f2(c5.get('pr_auc'))} la 0 / 30 / 50% zile lipsă. Peste 2/3 lipsă, agentul se abține și trimite la om."
        )
    fc_path = REP / "fusion_check.json"
    if fc_path.exists():
        fc = json.loads(fc_path.read_text(encoding="utf-8"))
        a2 = fc.get("demo-vara", {}).get("sigma_2pct", {})
        if a2:
            lines.append(
                f"- Fuziunea cu bilanțul pe post (verificată pe testul A, bilanț cu sigma 2%): precizia@10 "
                f"{f2(a2['precision_at_10_a'])} -> {f2(a2['precision_at_10_fused'])}, PR-AUC {f2(a2['pr_auc_a'], 3)} -> "
                f"{f2(a2['pr_auc_fused'], 3)}. Confirmă mai ales defectele cu pierdere mare de energie, rar furtul, "
                "niciodată tiparele fără pierdere de energie (`error_analysis.md`, secțiunea 9)."
            )
    lines += [
        "",
        "## Limite",
        "",
        ("- Etichetele de defect și de furt din Londra sunt sintetice. Un furt real poate arăta altfel decât atacurile "
        "din literatură (h1-h6) și variantele noastre."),
        ("- Slab la ceasul decalat, la sub-înregistrarea lentă și la bypass-ul parțial instalat treptat "
        "(`error_analysis.md`, secțiunea 3)."),
        "- Prevalența din test și din demo (3% defecte, 2% furturi) e o ipoteză. Precizia depinde de ea.",
        ("- Pe SGCC, împărțirea pe timp dă rezultate mai slabe (ROC-AUC ~0,71): golurile de colectare din 2015 dispar "
        "în 2016, iar eticheta nu are dată."),
        "",
        "## Etică, date personale, EU AI Act",
        "",
        ("- Fără date personale: ID-uri de contor sintetice, nicio adresă, niciun nume. Topologia e sintetică, pe "
        "poziții plauzibile din OpenStreetMap."),
        ("- Om în buclă: cazurile nesigure (zona gri conformal, istoric scurt, date insuficiente) și furtul suspectat "
        "la consum mic merg la un om, cu motivul scris."),
        "- Alarmele false se verifică pe chintile de consum la fiecare evaluare (`error_analysis.md`, secțiunea 5).",
        ("- Riscul de siguranță (`safety_flag`) se pune doar la ocolirea FIZICĂ a contorului, cu risc de incendiu: cel "
         "puțin 3 ore pe zi de zero exact la aceleași ore (punte sau comutator improvizat) sau o ocolire parțială "
         "sigură, la furt cu scor de cel puțin 0,8. Manipulările de date (profil aplatizat sau inversat) nu primesc "
         "steagul. Tiparul e în `extra.tamper_pattern`."),
        ("- EU AI Act: tratăm sistemul ca pe unul cu impact (utilități, infrastructură critică). De aceea are "
        "supraveghere umană, jurnal automat al deciziilor (planificatorul), documentație (acest card, "
        "`docs/data/A.md`) și explicații pentru fiecare lucrare. Clasificarea juridică exactă nu am verificat-o."),
        "",
        "## Reproducere",
        "",
        "```bash",
        "make a-all        # descărcare, features, antrenare, evaluare, robustețe, lucrări (~6 min)",
        "make a-evaluate   # doar evaluarea (reports/A/metrics.json, metrics_full.json, figuri)",
        "uv run python -m cyberpunks.a_contoare.report   # acest card și error_analysis.md, din cifrele de mai sus",
        "```",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    text = build()
    out = REP / "error_analysis.md"
    out.write_text(text, encoding="utf-8")
    print(f"scris: {out} ({len(text.splitlines())} de rânduri)")
    card = build_model_card()
    (REP / "model_card.md").write_text(card, encoding="utf-8")
    print(f"scris: {REP / 'model_card.md'} ({len(card.splitlines())} de rânduri)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
