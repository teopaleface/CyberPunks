"""Analiza erorilor bilanțului: unde greșesc modelele și de ce. Scrie `reports/bilant/error_analysis.md`.

    uv run python -m cyberpunks.a_bilant.error_analysis      # după evaluate (citește ferestrele salvate)
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from cyberpunks.a_bilant.problems import CLASS_RO
from cyberpunks.common.paths import DATA_PROCESSED, REPORTS

OUT = REPORTS / "bilant"


def _ro(x: float, d: int = 2) -> str:
    """Număr în format românesc: virgulă zecimală, punct la mii."""
    return f"{x:,.{d}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def _pct(x: float, d: int = 0) -> str:
    return _ro(x * 100, d) + "%"


def _tbl(df: pd.DataFrame, fmt: str = "{:.2f}") -> str:
    cols = [str(c) for c in df.columns]
    lines = ["| " + " | ".join([df.index.name or ""] + cols) + " |", "|" + "|".join("---" for _ in range(len(cols) + 1)) + "|"]
    for idx, row in df.astype(object).iterrows():
        vals = [str(int(v)) if isinstance(v, (int, np.integer)) else fmt.format(v) if isinstance(v, float) else str(v) for v in row]
        lines.append("| " + " | ".join([str(idx)] + vals) + " |")
    return "\n".join(lines)


def onset_age(win: pd.DataFrame, plans: dict) -> np.ndarray:
    """Câte zile au trecut de la apariția problemei postului (sau a contorului cu problemă) la ziua ferestrei."""
    ages = np.full(len(win), np.nan)
    for i, (pid, day, cls) in enumerate(zip(win["post_id"], win["day"], win["true_class"], strict=True)):
        if cls == "normal":
            continue
        ons = [pr["onset_day"] for pr in plans[pid]["problems"] if pr["onset_day"] <= day and (cls == "contor_client") == (pr["kind"] in ("meter_fault", "meter_tamper"))]
        if ons:
            ages[i] = day - max(ons)
    return ages


def main() -> None:
    base = DATA_PROCESSED / "bilant"
    win = pd.read_parquet(base / "windows_pop.parquet")
    tec = pd.read_parquet(base / "normal_test_pop.parquet")
    fm = pd.read_parquet(base / "fusion_meters_train.parquet")
    real = pd.read_parquet(base / "fusion_real_a_demo.parquet")
    plans = json.loads((base / "pop" / "plans.json").read_text())
    posts = pd.read_parquet(base / "pop" / "posts.parquet").set_index("post_id")
    md = ["# Analiza erorilor: bilanț pe post", "", "SIMULARE pe date publice, gândită pentru datele PPC. Test: cele 300 de posturi din registrul C (rețele nevăzute la antrenare). Comanda: `make bilant-eval`.", ""]

    # 1. pierderea normală
    tec = tec.join(posts[["topology"]], on="post_id")
    tec["err"] = tec["short_kwh"] - tec["p50"]
    tec["abs_err"] = tec["err"].abs()
    tec["inside"] = (tec["short_kwh"] >= tec["p10"]) & (tec["short_kwh"] <= tec["p90"])
    tec["month"] = pd.to_datetime(tec["date"]).dt.month
    by_topo = tec.groupby("topology").agg(zile=("err", "size"), mae_kwh=("abs_err", "mean"), pierdere_medie_kwh=("short_kwh", "mean"), acoperire_p10_p90=("inside", "mean"))
    by_topo["mae_relativ"] = by_topo["mae_kwh"] / by_topo["pierdere_medie_kwh"]
    by_topo.index.name = "topologia SimBench"
    by_month = tec.groupby("month").agg(mae_kwh=("abs_err", "mean"), pierdere_medie_kwh=("short_kwh", "mean"), acoperire_p10_p90=("inside", "mean"))
    by_month.index.name = "luna"
    post_bias = tec.groupby("post_id")["err"].mean()
    md += [
        "## 1. Pierderea normală",
        "",
        "Pe tipuri de rețea:",
        "",
        _tbl(by_topo),
        "",
        "Pe luni (vara are prosumatori care injectează, iarna are încălzire):",
        "",
        _tbl(by_month),
        "",
        f"- Cea mai mare parte a erorii e o abatere fixă pe post: media erorii pe post are abaterea standard {post_bias.std():.2f} kWh/zi, iar eroarea zilnică totală are MAE {tec['abs_err'].mean():.2f}. Abaterea vine din „vârsta” rețelei (factorul necunoscut de ±35% din simulare), pe care istoricul postului o prinde doar parțial.",
        f"- {(post_bias.abs() > 5).sum()} posturi au o abatere medie peste 5 kWh/zi. Acolo, o problemă mică (un contor de 3-4 kWh/zi) se pierde în eroare. De aceea fuziunea folosește creșterea lipsei, nu nivelul ei.",
        f"- Eroarea relativă cea mai mare o are topologia {by_topo['mae_relativ'].idxmax()} ({by_topo['mae_relativ'].max():.0%} din pierderea medie), cea mai mică {by_topo['mae_relativ'].idxmin()} ({by_topo['mae_relativ'].min():.0%}). Iarna (decembrie-ianuarie) eroarea crește odată cu încărcarea, pentru că pierderea crește cu pătratul ei.",
        "",
    ]

    # 2. diagnosticul
    win["age"] = onset_age(win, plans)
    win["ok"] = win["label"] == win["true_class"]
    win["rule_ok"] = win["rule"] == win["true_class"]
    prob = win[win["true_class"] != "normal"].copy()
    prob["varsta"] = pd.cut(prob["age"], [-1, 3, 7, 14, 30, 90, 400], labels=["0-3 zile", "4-7", "8-14", "15-30", "31-90", "peste 90"])
    by_age = prob.groupby("varsta", observed=True).agg(ferestre=("ok", "size"), corect_model=("ok", "mean"), corect_reguli=("rule_ok", "mean"))
    by_age.index.name = "de când există problema"
    prob["marime"] = pd.cut(prob["true_excess_kwh"].abs(), [0, 2, 5, 10, 25, 1e9], labels=["sub 2 kWh/zi", "2-5", "5-10", "10-25", "peste 25"])
    by_size = prob.groupby("marime", observed=True).agg(ferestre=("ok", "size"), corect_model=("ok", "mean"), corect_reguli=("rule_ok", "mean"))
    by_size.index.name = "lipsa reală"
    wrong = win[~win["ok"]]
    pairs = wrong.groupby(["true_class", "label"]).size().sort_values(ascending=False).head(8)
    pair_lines = [f"- {CLASS_RO[a]} → {CLASS_RO[b]}: {n} ferestre" for (a, b), n in pairs.items()]
    ab = win[win["abstain"]]
    na = win[~win["abstain"]]
    md += [
        "## 2. Diagnosticul cauzei",
        "",
        "Corect, după cât timp a trecut de la apariția problemei (fereastra are 14 zile):",
        "",
        _tbl(by_age),
        "",
        "Corect, după mărimea lipsei reale:",
        "",
        _tbl(by_size),
        "",
        "Confuziile cele mai dese:",
        "",
        *pair_lines,
        "",
        f"- „Nu sunt sigur”: modelul se abține în {len(ab) / len(win):.1%} din ferestre. Acolo ar fi avut dreptate în {ab['ok'].mean():.0%} din cazuri, iar în rest în {na['ok'].mean():.0%}. Abținerea scoate deci cazurile grele și le trimite la om.",
        "- Problemele foarte noi (0-3 zile) se văd greu: fereastra are încă puține zile cu problemă. Cele foarte vechi (peste 90 de zile) intră treptat în istoricul postului, care învață „normalul” cu tot cu problemă. Pe date reale, istoricul trebuie învățat doar din perioade verificate (după vizita echipei), nu din toate zilele.",
        f"- Cele mai dese confuzii sunt între contorul de client și pierderea normală, în ambele sensuri. Cauza e mărimea: un contor de client lipsește adesea doar câțiva kWh pe zi, cât eroarea pierderii normale (vezi tabelul pe mărimi). Sub 2 kWh/zi, modelul are dreptate doar în {by_size['corect_model'].iloc[0]:.0%} din cazuri.",
        "- Clientul la postul greșit se confundă cel mai des cu contorul de client: la postul cu lipsă, un client „dispare” din bază, iar semnătura seamănă cu un contor oprit. Le desparte vecinul cu surplus egal, dar semnalul dispare când vecinul are și el o problemă sau când surplusul e mic față de eroarea pierderii normale.",
        "- Contorul de post setat greșit (×2) e prins aproape mereu: raportul post/clienți e un semnal foarte curat.",
        "",
    ]

    # 3. fuziunea
    fm["rank_a"] = fm.groupby("day")["a"].rank(ascending=False)
    fm["rank_f"] = fm.groupby("day")["fused"].rank(ascending=False)
    pos = fm[fm["truth"]]
    up = (pos["rank_f"] < pos["rank_a"]).mean()
    small = pos[pos["drop"] < 2]
    real["confirmed"] = real["fused"] > real["a"] + 1e-9
    by_kind = real[real["truth"]].groupby("kind").agg(contoare=("truth", "size"), confirmate=("confirmed", "mean")).sort_values("contoare", ascending=False)
    by_kind.index.name = "tipul problemei (A)"
    fp = real[~real["truth"]]
    md += [
        "## 3. Fuziunea cu A (cu bilanț față de fără)",
        "",
        "Regula din producție: bilanțul doar confirmă (urcă scorul), nu coboară niciodată un contor găsit de A.",
        "",
        "### Pe mai multe zile, scoruri A simulate (lotul train)",
        "",
        f"- Contoarele cu problemă reală urcă în clasament după fuziune în {up:.0%} din cazuri.",
        f"- Cele care nu urcă au de obicei o lipsă mică: {len(small)} din {len(pos)} au sub 2 kWh/zi consum dispărut. Creșterea lipsei la post nu se deosebește atunci de zgomot (incertitudinea pe 7 zile e de câțiva kWh/zi).",
        "",
        "### Ziua demo, scorurile reale ale lui A (lotul pop)",
        "",
        f"- Din {int(real['truth'].sum())} contoare cu problemă reală, bilanțul confirmă {real.loc[real['truth'], 'confirmed'].mean():.0%}; din {len(fp)} fără problemă, confirmă {fp['confirmed'].mean():.0%}. Bilanțul confirmă deci de {real.loc[real['truth'], 'confirmed'].mean() / max(fp['confirmed'].mean(), 1e-9):.1f} ori mai des un contor cu problemă reală.",
        "",
        "Pe tipuri de problemă (cele care nu schimbă totalul zilei, ca profilul inversat sau ceasul decalat, nu pot fi confirmate de bilanț):",
        "",
        _tbl(by_kind),
        "",
        "- De ce câștigul e mic cu scorurile reale: A e deja foarte precis în vârful listei (100% în primele 200 de contoare), iar defectele lui A apar pe posturi cu câte 3-4 contoare cu probleme deodată (5,5% din contoare). Creșterea lipsei de la post e suma lor, deci nu spune care contor e de vină. Mai mult, curbele de consum ale lui A (Londra) nu sunt curbele clienților din lumea bilanțului; cele două lumi împart doar contorul cu problemă și ziua în care a apărut.",
        "- Limită: scorurile din testul pe mai multe zile sunt simulate (`fusion_eval.py`).",
        "",
    ]
    # 4. sinteza: unde ajută bilanțul și unde nu
    mj = json.loads((OUT / "metrics.json").read_text())
    M, B = mj["metrics"], mj["baseline_metrics"]

    def pc(c: str, k: str) -> str:
        v = M.get(f"cauze_post_{c}_{k}")
        return f"{v:.0%}" if v is not None else "-"

    md += [
        "## 4. Unde ajută bilanțul și unde nu (sinteză cinstită)",
        "",
        "### Unde ajută",
        "",
        f"- **Cauzele pe care contoarele nu le văd deloc.** Doar contoarele (modelul A) găsesc 0 din aceste probleme, prin construcție: nu au cum să vadă un branșament direct, un cablu care pierde sau un contor de post setat greșit. Bilanțul găsește postul în: furt înainte de contor {pc('furt_inainte_contor', 'found')} (cauza corectă {pc('furt_inainte_contor', 'right_cause')}), pierdere tehnică {pc('pierdere_tehnica', 'found')} ({pc('pierdere_tehnica', 'right_cause')}), contorul postului setat greșit {pc('contor_bilant_setat', 'found')} ({pc('contor_bilant_setat', 'right_cause')}), client la postul greșit {pc('client_post_gresit', 'found')} ({pc('client_post_gresit', 'right_cause')}) din ferestrele de test.",
        f"- Energia: bilanțul găsește {M.get('cauze_post_energy_found_share', 0):.0%} din energia lipsă din aceste cauze, adică ~{_ro(M.get('cauze_post_lei_per_month_found', 0), 0)} lei pe lună pe cele 300 de posturi ale hărții (la 0,70 lei/kWh). Din posturile marcate, {M.get('cauze_post_false_alarm_share_of_found', 0):.0%} sunt de fapt normale.",
        f"- Pe ziua demo, {M.get('invizibil_share_invisible_to_meters', 0):.0%} din energia pierdută peste normal nu apare la niciun contor de client.",
        f"- Diagnosticul cauzei bate tabelul de reguli din concept: F1 macro {_ro(M['diagnoza_macro_f1'])} față de {_ro(B['diagnoza_macro_f1'])}. Clientul la postul greșit: {_ro(M['diagnoza_f1_client_post_gresit'])} (reguli {_ro(B['diagnoza_f1_client_post_gresit'])}), după trăsătura „oglindă” (lipsa la un post și surplusul la vecin, zi de zi) și legarea celor două capete ale perechii. Pierderea tehnică: {_ro(M['diagnoza_f1_pierdere_tehnica'])} (reguli {_ro(B['diagnoza_f1_pierdere_tehnica'])}).",
        "- Planul B (unde montăm întâi contoarele de bilanț): `reports/bilant/plan_b.md`.",
        f"- Când modelul de contoare e mai slab (calitatea SGCC, AUC 0,80), confirmarea din bilanț ridică lei recuperați în primele 10 verificări pe zi de la {B['fuziune_sgcc_value_lei_per_day_at_10']:.0f} la {M['fuziune_sgcc_value_lei_per_day_at_10']:.0f}.",
        "",
        "### Unde nu ajută",
        "",
        f"- **Clasarea contoarelor găsite deja de A.** Cu scorurile reale ale lui A, precizia în primele 10-300 contoare e 100% cu și fără bilanț. La K = 500 bilanțul nu ajută ({_pct(M['fuziune_a_real_precision_at_500_a'], 1)} fără, {_pct(M['fuziune_a_real_precision_at_500_fused'], 1)} cu). Cu scoruri simulate de calitatea lui A pe Londra, câștigul e mic: în primele 10, de la {_pct(B['fuziune_precision_at_10'], 1)} la {_pct(M['fuziune_precision_at_10'], 1)}, adică {_ro(M['fuziune_wasted_trips_avoided_per_day_at_10'])} deplasări degeaba evitate pe zi.",
        "- Pierderea tehnică veche (peste 60 de zile) sau mică (sub 10 kWh/zi) scapă des: istoricul postului o învață ca normală, iar comparația cu luna trecută nu mai vede saltul. Am încercat și comparația cu normalul fără istoric (doar GIS): pierderea tehnică a urcat puțin, F1 macro a scăzut puțin, deci n-am păstrat-o în model.",
        "- De ce: un post are adesea mai multe contoare cu probleme deodată, iar lipsa de la post e suma lor, deci nu arată care contor e de vină. Problemele mici (sub 2 kWh/zi) se pierd în zgomotul pierderii normale. Tipurile care nu schimbă totalul zilei (profil inversat, ceas decalat, salturi) nu se văd deloc în bilanț.",
        "- **Să coboare scorul unui contor** pe un post fără lipsă: pe scorurile reale ale lui A asta strica lista (AUC 0,918 → 0,907), așa că fuziunea doar confirmă.",
        "- **Să rezolve „nu sunt sigur” al lui A:** pe ziua demo, 0 din 5 cazuri corecte. Funcția e oprită.",
        f"- Contorul de client în lumea cu defectele lui A: F1 {_ro(M['diagnoza_f1_contor_client'])}. Multe tipuri ale lui A au lipsă mică sau zero la totalul zilei.",
        "",
    ]
    (OUT / "error_analysis.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
