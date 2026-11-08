"""O singură intrare ML: rapoarte, proveniență, verificarea cifrelor și teste.

make ml-check: verifică predicțiile din repo și execută testele, fără descărcări/antrenări lungi.
make ml-report: regenerează raportul din rezultatele existente, fără a pretinde că a reantrenat.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, f1_score

from cyberpunks.common.paths import DATA_PROCESSED, REPORTS, ROOT

OUT = REPORTS / "ml"
GROUPS = ("A", "B", "C", "bilant", "benchmark")
BENCH = REPORTS / "benchmark"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def compare(name: str, expected: float, observed: float, tolerance: float = 5.1e-5) -> dict:
    return {"check": name, "expected": float(expected), "observed": float(observed),
            "tolerance": tolerance, "passed": bool(np.isfinite(observed) and abs(expected - observed) <= tolerance)}


def verify_predictions() -> tuple[list[dict], list[str]]:
    """Recalculează scorurile primare, fără reantrenare. Lipsurile publice sunt erori, SGCC local e opțional."""
    checks, unavailable = [], []
    for name, models in [("bilant_v2", ["lightgbm", "catboost"]),
                         ("bilant_feederbw", ["lightgbm_tuned", "catboost"])]:
        report = load(BENCH / f"{name}.json")
        p = pd.read_parquet(BENCH / "predictions" / f"{name}_test.parquet")
        for model in models:
            checks.append(compare(f"{name}/{model}/macro_f1", report[model]["test"]["macro_f1"],
                                  f1_score(p.true_class, p[f"{model}_label"], average="macro")))
    holdout = load(BENCH / "bilant_holdout.json")
    p = pd.read_parquet(BENCH / "predictions/bilant_holdout_test.parquet")
    for key, column in [("model", "lightgbm_label"), ("baseline", "rules_label")]:
        checks.append(compare(f"bilant_holdout/{key}/macro_f1", holdout[key]["macro_f1"],
                              f1_score(p.true_class, p[column], average="macro")))
    meters = load(BENCH / "contoare.json")
    for variant in ["lcl_baza", "lcl_extins"]:
        p = pd.read_parquet(BENCH / "predictions" / f"contoare_{variant}_test.parquet")
        for key, sel in [("full_test", np.ones(len(p), dtype=bool)), ("subtle", p.subtle.to_numpy())]:
            for model in ["lightgbm", "catboost"]:
                checks.append(compare(f"{variant}/{key}/{model}/pr_auc", meters[variant][key][model]["pr_auc"],
                                      average_precision_score(p.problem[sel], p[f"{model}_score"][sel])))
    sgcc = DATA_PROCESSED / "benchmark" / "contoare_sgcc_test.parquet"
    if sgcc.exists():
        p = pd.read_parquet(sgcc)
        for model in ["lightgbm", "catboost"]:
            checks.append(compare(f"sgcc/{model}/pr_auc", meters["sgcc_real_labels"][model]["pr_auc"],
                                  average_precision_score(p.label, p[f"{model}_score"])))
    else:
        unavailable.append("SGCC: predicțiile individuale rămân locale (licență de redistribuire neclară); "
                           "raportul agregat este disponibil. Reproducere: make bench-contoare, după pregătirea datelor A.")
    storms = load(BENCH / "furtuni.json")
    for name, block in [("furtuni_test2025", storms["test_2025"]),
                        ("furtuni_convectie_test", storms["convection_experiment"]["with_convection"])]:
        p = pd.read_parquet(BENCH / "predictions" / f"{name}.parquet")
        for model in ["lightgbm", "xgboost"]:
            checks.append(compare(f"{name}/{model}/pr_auc", block[model]["pr_auc"],
                                  average_precision_score(p.event, p[f"{model}_p"])))
    for name, target, metric in [("tensiune", "vmax_day", "mae_pu"), ("tensiune_reala", "target", "mae_volts")]:
        report = load(BENCH / f"{name}.json")
        if name == "tensiune":
            paths = sorted((BENCH / "predictions").glob("tensiune_sim_*_test.parquet"))
            if len(paths) != 6:
                raise ValueError("Lipsesc predicțiile C pentru una sau mai multe dintre cele șase topologii")
            p = pd.concat([pd.read_parquet(path) for path in paths], ignore_index=True)
        else:
            p = pd.read_parquet(BENCH / "predictions" / f"{name}_test.parquet")
        for model, score in report["test"].items():
            checks.append(compare(f"{name}/{model}/{metric}", score[metric], float(np.abs(p[target]-p[model]).mean())))
    return checks, unavailable


def code_hashes() -> dict:
    paths = [p for base in [ROOT / "src/cyberpunks", ROOT / "tests"] for p in base.rglob("*.py")]
    return {str(p.relative_to(ROOT)): digest(p) for p in sorted(paths)}


def run_tests() -> dict:
    path = DATA_PROCESSED / "ml" / "tests.xml"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    args = [sys.executable, "-m", "pytest", "tests/a", "tests/b", "tests/c", "tests/bilant", "tests/benchmark",
            "tests/test_repo_size.py",
            f"--junitxml={path}"]
    before = code_hashes()
    proc = subprocess.run(args, cwd=ROOT, check=False)
    counts = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    if path.exists():
        for suite in ET.parse(path).getroot().iter("testsuite"):
            for k in counts:
                counts[k] += int(suite.attrib.get(k, 0))
    result = {"command": "uv run --group bench pytest tests/a tests/b tests/c tests/bilant tests/benchmark tests/test_repo_size.py",
              "created_at": datetime.now(ZoneInfo("Europe/Bucharest")).isoformat(), "exit_code": proc.returncode,
              "counts": counts, "code_hashes": before, "code_unchanged_during_run": before == code_hashes(),
              "scope": "Teste de cod ML; nu reprezintă reantrenarea tuturor experimentelor istorice."}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "tests.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    return result


def scalar_metrics(value, prefix=""):
    """Anexa arată toate comparațiile numerice, fără a umple pagini cu istoricul fiecărui trial."""
    ignored = ("params", "parametr", "importance", "importanta", "history", "istoric", "environment", "features",
               "confusion_matrix", "timing", "top_zone_days", "cases", "quantiles", "code_hashes")
    if isinstance(value, dict):
        for k, v in value.items():
            if not any(word in k for word in ignored) and k not in {"trials", "folds"}:
                yield from scalar_metrics(v, f"{prefix}.{k}" if prefix else k)
    elif isinstance(value, list):
        if len(value) <= 3 and all(isinstance(x, (int, float)) for x in value):
            yield prefix, str(value)
        elif value and isinstance(value[0], dict) and len(value) <= 30:
            for i, v in enumerate(value):
                yield from scalar_metrics(v, f"{prefix}[{v.get('varianta', i)}]")
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        yield prefix, f"{value:.6g}"


def build() -> bool:
    OUT.mkdir(parents=True, exist_ok=True)
    checks, unavailable = verify_predictions()
    sources = {}
    for group in GROUPS:
        for path in sorted((REPORTS / group).glob("*.json")):
            sources[str(path.relative_to(ROOT))] = {"sha256": digest(path), "data": load(path)}
    provenance = ROOT / "data/samples/C/feederbw_voltage_daily.json"
    sources[str(provenance.relative_to(ROOT))] = {"sha256": digest(provenance), "data": load(provenance)}
    tests = load(OUT / "tests.json") if (OUT / "tests.json").exists() else None
    tests_current = bool(tests and tests["code_hashes"] == code_hashes() and tests["code_unchanged_during_run"])
    evidence = {"generated_at": datetime.now(ZoneInfo("Europe/Bucharest")).isoformat(),
                "sources": sources, "prediction_checks": checks, "unavailable_local_checks": unavailable,
                "tests": tests, "tests_match_current_code": tests_current,
                "prediction_hashes": {p.name: digest(p) for p in sorted((BENCH / "predictions").glob("*.parquet"))}}
    (OUT / "evidence.json").write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n")
    lines = ["# Machine learning — sursa comună de dovezi", "",
             ("Generat prin `make ml-report`. `evidence.json` reunește integral toate rapoartele JSON A, B, C, bilanț și "
             "benchmark, cu SHA256, predicții verificate și rezultatul testelor. Anexa de mai jos reunește comparațiile numerice."), "",
             "## Verificare", "",
             f"- Scoruri recalculate din predicții: **{sum(c['passed'] for c in checks)}/{len(checks)}**.",
             f"- Teste pe codul curent: **{'DA' if tests_current else 'NU / rulare necesară'}**."]
    if tests:
        lines += [f"- Ultima rulare: {tests['created_at']}; rezultat {tests['counts']}; cod ieșire {tests['exit_code']}."]
    lines += [f"- {note}" for note in unavailable]
    lines += ["", "```sh", "uv sync --group bench", "make ml-check   # teste + verificare cifre + raport, fără descărcări",
              "make ml-report  # doar verificare cifre și regenerare din dovezile existente", "```", "",
              ("Testele de cod și recalcularea scorurilor nu sunt o reantrenare. Experimentele istorice păstrează data și "
              "versiunea originală. Un test folosit repetat pentru decizii nu mai este un test final neatins."), "",
              "## Datele și etichetele", "",
              "| Sarcină | Intrări | Etichete | Separare / limită |", "|---|---|---|---|",
              "| Contoare LCL | consum real Londra | defecte și manipulări INJECTATE | gospodării și timp separate |",
              "| Contoare SGCC | consum real | furt REAL | clienți separați; testul temporal este mai slab |",
              "| Furtuni | EAGLE-I + vreme reală | întreruperi REALE, nu cauză de furtună confirmată | ani și state separate; vreme din arhivă |",
              "| Tensiune C | vreme reală + rețele SimBench | SINTETICE, simulare fizică | topologii și timp separate |",
              "| Bilanț v2 | rețele și măsurători simulate | cauze SINTETICE | posturi/cartiere separate |",
              "| Bilanț FeederBW | forma consumului măsurată | cauze SINTETICE | plecări reale separate |",
              "| Tensiune FeederBW, nou | tensiune monofazată măsurată | maxim zilnic REAL | plecări și timp separate; altă sarcină decât C |", "",
              "Datele sintetice sunt permise de barem. C și bilanțul nu devin validate în teren doar prin adăugarea unei surse reale.", "",
              "## Modelele livrate și metodele simple", "",
              "| Problemă | Metrică | Model | Baseline |", "|---|---|---:|---:|"]
    for group, metric in [("A", "subtle_precision_at_k"), ("A", "sgcc_pr_auc"), ("B", "pr_auc"),
                          ("C", "mae_vmax_pu"), ("C", "pr_auc_exceed"), ("bilant", "normal_mae_kwh_day")]:
        d = sources[f"reports/{group}/metrics.json"]["data"]
        if metric in d["metrics"] and metric in d["baseline_metrics"]:
            lines.append(f"| {group} | {metric} | {d['metrics'][metric]:.5f} | {d['baseline_metrics'][metric]:.5f} |")
    v2 = sources["reports/bilant/v2_comparison.json"]["data"]
    bbase = sources["reports/bilant/metrics.json"]["data"]["baseline_metrics"]["diagnoza_macro_f1"]
    holdout = sources["reports/benchmark/bilant_holdout.json"]["data"]
    lines += [f"| Bilanț v2 | macro-F1 | {v2['v2_cautare_optuna']['macro_f1']:.5f} | {bbase:.5f} |",
              (f"| Bilanț, lot nou fixat înainte de generare | macro-F1 | {holdout['model']['macro_f1']:.5f} | "
              f"{holdout['baseline']['macro_f1']:.5f} |"), "",
              "Scorurile experimentelor cu date extinse nu sunt automat scorurile modelului livrat.", "",
              "### Audit suplimentar al bilanțului", "",
              (f"{holdout['posts']} posturi noi, {holdout['rows']} ferestre, 60 cartiere; protocolul și SHA256 ale "
              "modelului/codului au fost fixate în commitul `3deadcc`, înainte de generarea lotului. "
              "Modelul livrat și regulile au rămas fixe; fără tuning sau selecție pe noul rezultat."), "",
              (f"Câștigul față de regulile simple: {holdout['delta_macro_f1']['delta']:.4f} macro-F1, "
              f"IC90 pe cartiere {holdout['delta_macro_f1']['ci90']}. "
              f"Abținere: {holdout['abstain_share']:.1%}; exactitate pe cazurile fără abținere: "
              f"{holdout['confident_accuracy']:.1%}. Macro-F1 de mai sus include toate cazurile, inclusiv abținerile."), "",
              ("Lotul folosește același simulator și aceleași familii de topologii; distribuția defectelor diferă "
              "de harta demo. Scorul nou este o verificare separată, nu o îmbunătățire măsurată pe testul vechi "
              "și nu o validare pe cauze reale."), "",
              "## Ce au schimbat datele și Optuna", "",
              "| Experiment | Metrică | Înainte | După |", "|---|---|---:|---:|"]
    a = sources["reports/A/experiments_extra.json"]["data"]["rows"]
    for row in a:
        lines.append(f"| A: {row['varianta']} | PR-AUC subtil | {a[0]['subtle_pr_auc']:.4f} | {row['subtle_pr_auc']:.4f} |")
    b = sources["reports/B/experiments_extra.json"]["data"]["rows"]
    for row in b:
        lines.append(f"| B: {row['varianta']} | PR-AUC | {b[0]['pr_auc']:.4f} | {row['pr_auc']:.4f} |")
    c = sources["reports/C/experiments_extra.json"]["data"]["rows"]
    for row in c:
        for dataset, score in row.items():
            if isinstance(score, dict) and "mae_vmax_pu" in score:
                lines.append(f"| C: {row['varianta']}, {dataset} | MAE pu | — | {score['mae_vmax_pu']:.5f} |")
    for label, key in [("A", "reports/A/tuning_optuna.json"), ("B", "reports/B/tuning_optuna_b_ani2023-2024.json"),
                       ("B convecție", "reports/B/tuning_optuna_b_convectie_ani2023-2024.json")]:
        d = sources[key]["data"]
        te = d.get("test", d.get("test_2025"))
        metric = "subtle_pr_auc" if label == "A" else "pr_auc"
        lines.append(f"| Optuna {label} | {metric} | {te['livrat'][metric]:.5f} | {te['gasit'][metric]:.5f} |")
    ct = sources["reports/C/tuning_optuna_mai_multe_regiuni.json"]["data"]["test_2025"]
    lines += [(f"| Optuna C | MAE pu | {ct['livrat']['bucuresti_2025']['mae_vmax_pu']:.5f} | "
              f"{ct['gasit']['bucuresti_2025']['mae_vmax_pu']:.5f} |"),
              (f"| Optuna bilanț v2 | macro-F1 | {v2['mai_multe_posturi_si_trasaturi_noi']['macro_f1']:.5f} | "
              f"{v2['v2_cautare_optuna']['macro_f1']:.5f} |"), "",
              ("Concluzia corectă: Optuna nu ajută uniform. A/B nu confirmă un câștig; C are un câștig mic, "
              "iar bilanțul v2 crește. Intervalele și protocoalele exacte sunt în anexă."), "",
              "## CatBoost și XGBoost", ""]
    # Tabelele existente sunt generate din JSON; copiem conținutul în intrarea comună, cu ancore locale.
    from cyberpunks.benchmark.report import main as benchmark_tables
    benchmark_tables()
    lines += [(BENCH / "tabele.md").read_text().replace("# Tabelele benchmarkului (generate)", "### Comparațiile A/B/bilanț")]
    for name, metric, title in [("tensiune", "mae_pu", "C: aceeași simulare, buget fix"),
                                ("tensiune_reala", "mae_volts", "FeederBW: tensiuni măsurate")]:
        d = sources[f"reports/benchmark/{name}.json"]["data"]
        lines += [f"### {title}", "", d["protocol"], "", "| Model | MAE (mai mic = mai bine) |", "|---|---:|"]
        lines += [f"| {m} | {s[metric]:.6f} |" for m, s in d["test"].items()]
        if name == "tensiune_reala":
            lines += ["", (f"Ales înaintea testului, pe validare: **{d['selected_on_validation']}**. "
                      f"Test: {d['test_rows']} zile-plecare, {d['test_days_above_253V']} peste 253 V. "
                      "Ridge este mai bun pe test; asta nu justifică schimbarea retroactivă a selecției. "
                      "Acest experiment nu probează detectarea supratensiunilor, nici maximul spațial al C.")]
        lines.append("")
    lines += ["## Erori și limite care rămân", "",
              "- Bilanț: contorul de client și pierderea tehnică rămân clasele slabe; nu există aici cauze confirmate de echipe în teren.",
              "- C: recall scăzut pe semiurb4 la pragul 0,5. Nu mutăm pragul după ce am văzut testul; sunt necesare date operaționale.",
              "- B: testul românesc este scurt, fără furtuni severe; nu susține un câștig de transfer. Vremea arhivată nu reproduce erorile unei prognoze.",
              "- SGCC: rezultatul pe clienți separați este mai bun decât în separarea temporală. Nu promitem aceeași precizie în România.",
              "- IC90 care include zero înseamnă diferență neconcludentă, nu echivalență demonstrată. Comparațiile multiple sunt exploratorii.", "",
              "## Reproducere completă și date locale", "",
              ("`make ml-check` funcționează cu datele mici/predicțiile din Git. SGCC se verifică suplimentar când există local. "
              "Pentru reantrenare, comenzile și sursele sunt în fiecare fișă; datele mari nu sunt ascunse drept dependențe ale testelor rapide."), "",
              "| Scop | Comandă | Pregătire |", "|---|---|---|",
              "| CatBoost bilanț | `make bench-bilant` | lot trainL/pop + FeederBW: vezi `reports/benchmark/RAPORT.md` |",
              "| CatBoost contoare | `make bench-contoare` | SGCC local, LCL 168 fișiere și mostre procesate A |",
              "| XGBoost furtuni | `make bench-furtuni` | setul B și meteo convecție |",
              "| C, trei algoritmi | `make bench-tensiune` | `make c-weather c-sim` sau cache experiment C |",
              "| Audit bilanț, model fixat | `make bench-bilant-holdout` | vremea C (`make c-weather`); protocolul este deja în Git |",
              "| Tensiune măsurată, trei algoritmi | `make bench-tensiune-reala` | agregatul CC BY 4.0 inclus în Git |",
              "| Refacere agregat FeederBW | `uv run --group bench python -m cyberpunks.benchmark.tensiune_reala --prepare` | `uv run python -m cyberpunks.a_bilant.feederbw download` |", "",
              "## Anexă: toate comparațiile și verificările", "",
              ("Istoricul complet al trialurilor și metadatele sunt păstrate în `evidence.json`. Valorile de mai jos provin direct din surse; "
              "nu am amestecat seturi de test diferite într-un scor comun."), ""]
    for source, entry in sources.items():
        lines += [f"<details><summary>{source}</summary>", "", f"[Sursa](../../{source}) · SHA256 `{entry['sha256']}`", "",
                  "| Câmp | Valoare |", "|---|---:|"]
        lines += [f"| {key} | {value} |" for key, value in scalar_metrics(entry["data"])]
        lines += ["", "</details>", ""]
    lines += ["### Recalcularea predicțiilor", "", "| Verificare | Raportat | Recalculat | OK |", "|---|---:|---:|---|"]
    lines += [f"| {c['check']} | {c['expected']:.6f} | {c['observed']:.6f} | {c['passed']} |" for c in checks]
    (OUT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return all(c["passed"] for c in checks)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tests", action="store_true")
    args = parser.parse_args()
    tests = run_tests() if args.tests else None
    ok = build()
    if tests:
        ok &= tests["exit_code"] == 0 and tests["code_unchanged_during_run"] and tests["counts"]["tests"] > 0
    print(f"Raport: {OUT / 'README.md'}; verificare {'OK' if ok else 'EȘUATĂ'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
