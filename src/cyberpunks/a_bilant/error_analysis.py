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
    fm = pd.read_parquet(base / "fusion_meters_pop.parquet")
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
    share = fm["drop"] / fm["before"].abs().clip(lower=0.5)
    benign = fm[(fm["benign"] != "") & (share > 0.5) & ~fm["truth"]]
    md += [
        "## 3. Fuziunea cu A (cu bilanț față de fără)",
        "",
        f"- Contoarele cu problemă reală urcă în clasament după fuziune în {up:.0%} din cazuri.",
        f"- Cele care nu urcă au de obicei o lipsă mică: {len(small)} din {len(pos)} au sub 2 kWh/zi consum dispărut. Creșterea lipsei la post nu se deosebește atunci de zgomot (incertitudinea pe 7 zile e de câțiva kWh/zi).",
        f"- Consumul scăzut real (concediu, ocupare schimbată, cu consumul scăzut la mai puțin de jumătate și fără defect): {len(benign)} rânduri contor-zi. Mediana rangului lor trece de la {benign['rank_a'].median():.0f} la {benign['rank_f'].median():.0f} după fuziune (rang mai mare = mai jos în listă); în primele 20 pe zi ajung {((benign['rank_a'] <= 20).sum() / fm['day'].nunique()):.1f} fără bilanț și {((benign['rank_f'] <= 20).sum() / fm['day'].nunique()):.1f} cu bilanț.",
        "- Furtul înainte de contor ridică scorul tuturor contoarelor cu scădere de pe acel post, chiar dacă nu sunt de vină. De aceea fuziunea compară mărimea: urcă doar contorul a cărui scădere se potrivește cu lipsa.",
        "- Limită: scorurile A sunt simulate (vezi `fusion_eval.py`). Cifra se reface cu scorurile reale ale lui A când contoarele lui sunt legate de posturile registrului C.",
        "",
    ]
    (OUT / "error_analysis.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
