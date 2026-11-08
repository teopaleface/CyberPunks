"""Tabelele benchmarkului, generate din `reports/benchmark/*.json` (fără cifre scrise de mână).

    uv run python -m cyberpunks.benchmark.report       # scrie reports/benchmark/tabele.md

Verdictul automat: candidatul „bate” LightGBM doar dacă intervalul 90% al diferenței pe metrica principală e peste
zero ȘI nicio clasă importantă (furtul la bilanț; manipulările la contoare; clienții acoperiți la furtuni) nu are
intervalul sub zero. „Pierde” dacă intervalul e sub zero. Altfel „la egalitate statistică”.
"""

from __future__ import annotations

import json

from cyberpunks.benchmark.common import OUT

CLASSES_RO = {"normal": "normal", "contor_client": "contor de client", "furt_inainte_contor": "**furt înainte de contor**",
              "pierdere_tehnica": "pierdere tehnică", "client_post_gresit": "client la postul greșit",
              "contor_bilant_setat": "contor de bilanț setat greșit"}


BASE_RO = {"lightgbm": "LightGBM v2", "lightgbm_tuned": "LightGBM optimizat pe FeederBW"}


def load(name: str) -> dict | None:
    p = OUT / f"{name}.json"
    return json.loads(p.read_text()) if p.exists() else None


def f(x: float, nd: int = 4) -> str:
    return "—" if x is None else f"{x:.{nd}f}".replace(".", ",")


def ci(d: dict, nd: int = 4) -> str:
    z = " (include 0)" if d["includes_zero"] else ""
    return f"{f(d['delta'], nd)} [{f(d['ci90'][0], nd)}; {f(d['ci90'][1], nd)}]{z}"


def verdict(main: dict, guards: list[dict]) -> str:
    if main["ci90"][1] < 0:
        return "pierde"
    if main["ci90"][0] > 0 and all(g["ci90"][1] >= 0 for g in guards):
        return "bate"
    if main["ci90"][0] > 0:
        return "câștig mediu, dar scade pe o clasă importantă"
    return "la egalitate statistică"


def bilant_table(d: dict, base: str, cand: str, delta_key: str, title: str) -> list[str]:
    tb, tc = d[base]["test"], d[cand]["test"]
    dd = d[delta_key]
    rows = [f"### {title}", "", f"Etichete: {d['labels']}.", "",
            f"| Metrica | {BASE_RO.get(base, base)} | CatBoost | CatBoost − LightGBM, IC 90% |", "|---|---:|---:|---|",
            f"| F1 macro | {f(tb['macro_f1'])} | {f(tc['macro_f1'])} | {ci(dd['macro_f1'])} |",
            f"| exactitate | {f(tb['accuracy'])} | {f(tc['accuracy'])} | |"]
    for c, ro in CLASSES_RO.items():
        rows.append(f"| F1 {ro} | {f(tb['f1_by_class'][c])} | {f(tc['f1_by_class'][c])} | {ci(dd['f1_' + c])} |")
    v = verdict(dd["macro_f1"], [dd["f1_furt_inainte_contor"]])
    rows += ["", (f"Bootstrap: {d['bootstrap_unit']}. Clase mai slabe la CatBoost: "
             f"{', '.join(dd['classes_worse']) or 'niciuna'}; cu intervalul sub zero: "
             f"{', '.join(dd['classes_worse_ci_below_zero']) or 'niciuna'}. **Verdict CatBoost: {v}.**"), ""]
    for name, cm in (("LightGBM", tb), ("CatBoost", tc)):
        m = cm["confusion_matrix"]["matrix"]
        rows += [f"Matricea de confuzie {name} (rânduri = adevărat, coloane = prezis; ordinea claselor de mai sus):", "",
                 "| | " + " | ".join(f"p:{i + 1}" for i in range(len(m))) + " |", "|---" * (len(m) + 1) + "|"]
        rows += [f"| {i + 1}. {list(CLASSES_RO)[i]} | " + " | ".join(str(x) for x in r) + " |" for i, r in enumerate(m)]
        rows.append("")
    return rows


def contoare_rows(name: str, block: dict, real: bool) -> list[str]:
    rows = [f"### {name}", "", f"Etichete: {'REALE (SGCC)' if real else block['labels']}.", ""]
    if real:
        lg, cb, dd = block["lightgbm"], block["catboost"], block["delta_catboost_minus_lightgbm"]
        k = block["k_main"]
        rows += ["| Metrica | LightGBM | CatBoost | CatBoost − LightGBM, IC 90% |", "|---|---:|---:|---|",
                 f"| PR-AUC | {f(lg['pr_auc'])} | {f(cb['pr_auc'])} | {ci(dd['pr_auc'])} |",
                 f"| ROC-AUC | {f(lg['roc_auc'])} | {f(cb['roc_auc'])} | |"]
        for kk in block["ks"]:
            extra = ci(dd[f"precision_at_{k}"]) if kk == k else ""
            rows.append(f"| precizia la K={kk}{' (1%)' if kk == k else ''} | {f(lg['precision_at_k'][str(kk)])} | "
                        f"{f(cb['precision_at_k'][str(kk)])} | {extra} |")
        rows.append(f"| Brier (scor calibrat) | {f(lg['calibration']['brier'])} | {f(cb['calibration']['brier'])} | |")
        v = verdict(dd["pr_auc"], [dd[f"precision_at_{k}"]])
        rows += ["", f"Bootstrap: {block['bootstrap_unit']}. **Verdict CatBoost: {v}.**", ""]
        return rows
    full, sub, tam = block["full_test"], block["subtle"], block["tamper_only"]
    dd = block["delta_catboost_minus_lightgbm"]
    k, ks = block["k_main"], block["k_top1pct_subtle"]
    rows += [(f"Antrenare: {block['n_train']} eșantioane, {block['households_train']} gospodării. Test: {block['n_test']} "
             f"eșantioane, {block['households_test']} gospodării nevăzute."), "",
             "| Metrica | LightGBM | CatBoost | CatBoost − LightGBM, IC 90% |", "|---|---:|---:|---|",
             f"| **subtile: PR-AUC** | {f(sub['lightgbm']['pr_auc'])} | {f(sub['catboost']['pr_auc'])} | {ci(dd['subtle']['pr_auc'])} |",
             (f"| **subtile: precizia în top 1% (K={ks})** | {f(sub['lightgbm']['precision_top1pct'])} | "
             f"{f(sub['catboost']['precision_top1pct'])} | {ci(dd['subtle'][f'precision_at_{ks}'])} |")]
    for kk in sorted(int(x) for x in sub["lightgbm"]["precision_at_k"]):
        if kk != ks:
            rows.append(f"| subtile: precizia la K={kk} | {f(sub['lightgbm']['precision_at_k'][str(kk)])} | "
                        f"{f(sub['catboost']['precision_at_k'][str(kk)])} | |")
    rows += [f"| tot testul: PR-AUC | {f(full['lightgbm']['pr_auc'])} | {f(full['catboost']['pr_auc'])} | {ci(dd['full_test']['pr_auc'])} |",
             (f"| tot testul: precizia la K={k} (1%) | {f(full['lightgbm']['precision_at_k'][str(k)])} | "
             f"{f(full['catboost']['precision_at_k'][str(k)])} | {ci(dd['full_test'][f'precision_at_{k}'])} |")]
    for kk in sorted(int(x) for x in full["lightgbm"]["precision_at_k"]):
        if kk != k:
            rows.append(f"| tot testul: precizia la K={kk} | {f(full['lightgbm']['precision_at_k'][str(kk)])} | "
                        f"{f(full['catboost']['precision_at_k'][str(kk)])} | |")
    tk = next(x for x in dd["tamper_only"] if x.startswith("precision_at_"))
    rows += [f"| manipulări (furt) vs normale: PR-AUC | {f(tam['lightgbm']['pr_auc'])} | {f(tam['catboost']['pr_auc'])} | {ci(dd['tamper_only']['pr_auc'])} |",
             f"| manipulări vs normale: precizia la 1% | {f(tam['lightgbm']['precision_at_k'])} | {f(tam['catboost']['precision_at_k'])} | {ci(dd['tamper_only'][tk])} |",
             f"| Brier (tot testul) | {f(full['lightgbm']['calibration']['brier'])} | {f(full['catboost']['calibration']['brier'])} | |"]
    v = verdict(dd["subtle"]["pr_auc"], [dd["tamper_only"]["pr_auc"], dd["subtle"][f"precision_at_{ks}"]])
    rows += ["", f"Bootstrap: gospodăriile de test. **Verdict CatBoost: {v}.**", ""]
    return rows


def furtuni_rows(block: dict, title: str) -> list[str]:
    lg, xg, dd = block["lightgbm"], block["xgboost"], block["delta_xgboost_minus_lightgbm"]
    cap = block["capacity"]["results"]
    k = block["capacity"]["k_crews_per_day"]
    rows = [f"### {title}", "", "| Metrica | LightGBM | XGBoost | XGBoost − LightGBM, IC 90% |", "|---|---:|---:|---|",
            f"| PR-AUC | {f(lg['pr_auc'])} | {f(xg['pr_auc'])} | {ci(dd['pr_auc'])} |",
            f"| Brier (mai mic = mai bine) | {f(lg['brier'])} | {f(xg['brier'])} | {ci(dd['brier'], 5)} |",
            (f"| clienți afectați acoperiți, {k} echipe/zi | {f(cap['lightgbm']['customers_covered_share'])} | "
            f"{f(cap['xgboost']['customers_covered_share'])} | {ci(dd['customers_covered_share'])} |"),
            f"| evenimente prinse, {k} echipe/zi | {f(cap['lightgbm']['events_caught_share'])} | {f(cap['xgboost']['events_caught_share'])} | |",
            f"| ROC-AUC | {f(lg['roc_auc'])} | {f(xg['roc_auc'])} | |",
            f"| recall la prag (prag din OOF) | {f(lg['recall_at_thr'])} | {f(xg['recall_at_thr'])} | |",
            f"| recall pe zilele severe, la prag | {f(lg['recall_severe_at_thr'])} | {f(xg['recall_severe_at_thr'])} | |",
            f"| alerte la 100 zone-zile | {f(lg['alerts_per_100_zone_days'], 2)} | {f(xg['alerts_per_100_zone_days'], 2)} | |",
            "", (f"Referințe la același buget: aleator {f(cap['aleator']['customers_covered_share'])}, oracol "
            f"{f(cap['oracol']['customers_covered_share'])}. Bootstrap pe săptămânile din 2025. "
            f"**Verdict XGBoost: {verdict(dd['pr_auc'], [dd['customers_covered_share']])}.**"), ""]
    return rows


def main() -> int:
    lines = ["# Tabelele benchmarkului (generate)", "",
             ("Generat de `python -m cyberpunks.benchmark.report` din `reports/benchmark/*.json`. Diferențele sunt "
             "candidat − LightGBM, cu interval bootstrap 90% pe grupuri. „(include 0)” = diferența nu e sigură."), ""]
    b = load("bilant_v2")
    if b:
        lines += ["## 1. Bilanț pe post (diagnostice SINTETICE)", ""]
        lines += bilant_table(b, "lightgbm", "catboost", "delta_catboost_minus_lightgbm", "1a. Testul v2 (300 de posturi, 13.200 de ferestre)")
    fb = load("bilant_feederbw")
    if fb:
        lines += bilant_table(fb, "lightgbm_tuned", "catboost", "delta_catboost_minus_lightgbm_tuned",
                              "1b. FeederBW, split pe plecarea reală (LightGBM optimizat, același buget)")
        d2 = fb["delta_catboost_minus_lightgbm_v2params"]
        lines += [(f"Față de LightGBM cu setările v2 (fără căutare pe FeederBW): F1 macro {ci(d2['macro_f1'])}; "
                  f"furt înainte de contor {ci(d2['f1_furt_inainte_contor'])}."), ""]
    c = load("contoare")
    if c:
        lines += ["## 2. Contoare", ""]
        lines += contoare_rows("2a. SGCC, etichete REALE de furt", c["sgcc_real_labels"], real=True)
        lines += contoare_rows("2b. Low Carbon London, 45 de fișiere (probleme INJECTATE)", c["lcl_baza"], real=False)
        if "lcl_extins" in c:
            lines += contoare_rows("2c. Low Carbon London extins, 168 de fișiere (probleme INJECTATE)", c["lcl_extins"], real=False)
    s = load("furtuni")
    if s:
        lines += ["## 3. Furtuni (date REALE, SUA)", ""]
        lines += furtuni_rows(s["test_2025"], "3a. Test 2025, an nevăzut")
        if "unseen_states" in s:
            u = s["unseen_states"]
            lines += ["### 3b. State nevăzute (fiecare stat scos din antrenare, test pe 2025)", "",
                      "| Stat | Evenimente | PR-AUC LightGBM | PR-AUC XGBoost | Brier LightGBM | Brier XGBoost |", "|---|---:|---:|---:|---:|---:|"]
            lines += [f"| {st} | {r['events']} | {f(r['lightgbm_pr_auc'])} | {f(r['xgboost_pr_auc'])} | {f(r['lightgbm_brier'])} | "
                      f"{f(r['xgboost_brier'])} |" for st, r in u["per_state"].items()]
            lines += ["", (f"Media pe {u['states']} state: LightGBM {f(u['lightgbm_pr_auc_mean'])}, XGBoost "
                      f"{f(u['xgboost_pr_auc_mean'])}; diferența medie {ci(u['delta_mean_pr_auc'])}; XGBoost mai bun în "
                      f"{u['states_xgboost_better']} din {u['states']} state. "
                      f"**Verdict XGBoost: {verdict(u['delta_mean_pr_auc'], [])}.**"), ""]
        cx = s.get("convection_experiment", {})
        if "with_convection" in cx:
            lines += furtuni_rows(cx["with_convection"], "3c. Experiment separat: ambele modele cu variabilele de convecție")
            g = cx["convection_gain_per_model"]
            lines += [f"Câștigul convecției, pe același test: LightGBM {ci(g['lightgbm']['delta'])}, XGBoost {ci(g['xgboost']['delta'])}.", ""]
    (OUT / "tabele.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"scris: {OUT / 'tabele.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
