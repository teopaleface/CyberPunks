"""Planul B: unde se montează întâi contoarele de bilanț, când nu toate posturile au unul.

Fără contor de post, lipsa nu se vede. Estimăm energia intrată în post din modelul rețelei (suma clienților plus
pierderea normală fără istoric, `normal_cold`) și clasăm posturile după lipsa așteptată, dintr-un model antrenat pe
posturile care au contor de bilanț (lotul `train`), doar cu ce se vede fără el: semnalele contoarelor de client
(zile cu zero, blocate, negative noaptea, consum dispărut), mărimea postului, cablurile din GIS, pierderea tehnică
estimată.

Comparăm, pe cele 300 de posturi ale hărții (`pop`), ce parte din energia lipsă reală (din construcție, ultimele 90
de zile) se găsește montând contoare la primele k posturi: modelul față de alegerea la întâmplare, „posturile mari
întâi” și „pierderea tehnică estimată cea mai mare întâi”.

    uv run python -m cyberpunks.a_bilant.planb      # scrie reports/bilant/plan_b.md, plan_b.png, plan_b_ranking.csv
"""

from __future__ import annotations

import json

import lightgbm as lgb
import numpy as np
import pandas as pd

from cyberpunks.a_bilant import features as F
from cyberpunks.a_bilant import normal as N
from cyberpunks.common.config import load as load_config
from cyberpunks.common.paths import DATA_PROCESSED, REPORTS

OUT = REPORTS / "bilant"
LAST = 90
PB_FEATURES = ["abs_kwh", "p50_cold", "zero_days", "stuck_days", "neg_days", "n_drop50", "max_drop_kwh", "miss_share", *F.STATIC]
SMART_METER_SHARE = {"Dobrogea": 0.6685, "Muntenia": 0.5881, "Banat": 0.5645}  # 31 dec. 2025, infobuz (memory/12)


def post_table(pool: str, models: dict) -> pd.DataFrame:
    d = F.load_pool(pool)
    D = int(d["day"].max()) + 1
    w = d[d["day"] >= D - LAST].copy()
    w["p50_cold"] = models["cold"].predict(N.drop_history(w))["p50"].to_numpy()
    w["p50_warm"] = N.predict_any(models, w)["p50"].to_numpy()
    cfg = w.groupby("post_id")["true_class"].apply(lambda s: (s == "contor_bilant_setat").any())
    g = w.groupby("post_id")
    t = pd.DataFrame(
        {
            "abs_kwh": g["abs_kwh"].mean(),
            "p50_cold": g["p50_cold"].mean(),
            "zero_days": g["cnt_zero"].sum(),
            "stuck_days": g["cnt_stuck"].sum(),
            "neg_days": g["cnt_neg_night"].sum(),
            "miss_share": g["miss_share"].mean(),
            "measured_excess": (g["short_kwh"].mean() - g["p50_warm"].mean()),
            "true_excess": g["true_excess_kwh"].mean(),
        }
    )
    for c in F.STATIC:
        t[c] = g[c].first()
    cust = np.load(DATA_PROCESSED / "bilant" / pool / "cust_daily.npz")
    nd, md = [], []
    for pid in t.index:
        cd = cust[pid].astype(float)
        a, b = cd[:, D - LAST : D - LAST + 30].mean(1), cd[:, D - 30 : D].mean(1)
        drop = a - b
        nd.append(int(((drop / np.maximum(np.abs(a), 0.5)) > 0.5).sum()))
        md.append(float(max(drop.max(), 0.0)))
    t["n_drop50"] = nd
    t["max_drop_kwh"] = md
    t["config_problem"] = cfg
    return t[~t["config_problem"]]  # contorul de post setat greșit nu există unde nu e contor de post


def md_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    out += ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(out)


def capture_curve(t: pd.DataFrame, score: np.ndarray) -> np.ndarray:
    """Ce parte din lipsa reală totală (pozitivă) e la primele k posturi, pentru k = 1..n."""
    ex = t["true_excess"].clip(lower=0).to_numpy()
    order = np.argsort(-score)
    return np.cumsum(ex[order]) / ex.sum()


def main() -> None:
    models = {"warm": N.load("normal"), "cold": N.load("normal_cold")}
    tr = post_table("train", models)
    te = post_table("pop", models)
    m = lgb.LGBMRegressor(objective="huber", alpha=5.0, n_estimators=300, learning_rate=0.03, num_leaves=15, min_child_samples=10, verbose=-1, n_jobs=4, random_state=0)
    m.fit(tr[PB_FEATURES], tr["measured_excess"])
    te["planb_score"] = m.predict(te[PB_FEATURES])
    n = len(te)
    rng = np.random.default_rng(0)
    rand = np.mean([capture_curve(te, rng.random(n)) for _ in range(200)], axis=0)
    curves = {
        "model (planul B)": capture_curve(te, te["planb_score"].to_numpy()),
        "posturile mari întâi": capture_curve(te, te["abs_kwh"].to_numpy()),
        "pierderea tehnică estimată întâi": capture_curve(te, te["p50_cold"].to_numpy()),
        "la întâmplare (media a 200 de trageri)": rand,
    }
    eco = load_config("economics")
    price = float(eco["energy"]["loss_cost_lei_per_kwh"])
    ks = [int(round(n * f)) for f in (0.1, 0.2, 0.33, 0.44)]
    rows = []
    for name, c in curves.items():
        rows.append({"metoda": name, **{f"primele {k} posturi ({k / n:.0%})": f"{c[k - 1] * 100:.1f}%" for k in ks}})
    tab = pd.DataFrame(rows)
    top = te.sort_values("planb_score", ascending=False)
    k20 = ks[1]
    found = top["true_excess"].clip(lower=0).iloc[:k20].sum()
    lei_year_per_meter = found * 365 * price / k20
    lei_year_random = te["true_excess"].clip(lower=0).mean() * 365 * price
    OUT.mkdir(parents=True, exist_ok=True)
    top[["planb_score", "abs_kwh", "p50_cold", "n_drop50", "zero_days", "true_excess"]].round(3).to_csv(OUT / "plan_b_ranking.csv")
    _fig(curves, n)
    summary = {
        "posts": n,
        "capture_top20pct_model": float(curves["model (planul B)"][k20 - 1]),
        "capture_top20pct_random": float(rand[k20 - 1]),
        "capture_top20pct_biggest": float(curves["posturile mari întâi"][k20 - 1]),
        "lei_year_per_meter_model_top20pct": float(lei_year_per_meter),
        "lei_year_per_meter_random": float(lei_year_random),
    }
    (OUT / "plan_b.json").write_text(json.dumps(summary, indent=2))
    md = f"""# Planul B: unde montăm întâi contoarele de bilanț

SIMULARE pe date publice, gândită pentru datele PPC. Comanda: `uv run python -m cyberpunks.a_bilant.planb` (după `make bilant-data bilant-eval`).

## De ce contează

Gradul de integrare a contoarelor inteligente la 31 decembrie 2025 (infobuz, prin `memory/12-probleme-reale-ppc-2026.md`): Dobrogea 66,85%, Muntenia 58,81%, Banat 56,45%. Ținta RER e 67% la finalul lui 2026. Planul de dezvoltare RER 2026-2035 cere ca infrastructura de contorizare inteligentă să permită cel puțin un contor de bilanț în fiecare post (`docs/research/bilant_lit.md`). Până atunci, o parte din posturi nu au bilanț complet. Concentratorul de date din post nu e contor de bilanț. Planul B răspunde la întrebarea: unde montăm întâi?

## Cum

1. Fără contor de post, energia intrată se estimează din modelul rețelei: suma clienților plus pierderea normală estimată fără istoric (`normal_cold`, eroare medie 12,0 kWh/zi pe rețele nevăzute, `reports/bilant/metrics.json`).
2. Un model (LightGBM, pierdere Huber) învață, pe cele 300 de posturi de antrenare care au contor de bilanț, lipsa măsurată peste normal din ultimele {LAST} de zile. Folosește doar ce se vede fără contorul postului: semnalele contoarelor de client (zile cu zero, blocate, negative noaptea, clienți cu consum scăzut la jumătate, cel mai mare consum dispărut), mărimea postului, cablurile din GIS și pierderea tehnică estimată.
3. Pe cele {n} posturi ale hărții (fără cele cu contorul de post setat greșit, care nu există unde nu e contor), comparăm ce parte din lipsa reală totală (din construcție) se găsește montând contoare la primele k posturi.

## Rezultat

{md_table(tab)}

- Cu modelul, primele 20% din posturi ({k20}) acoperă **{summary['capture_top20pct_model'] * 100:.0f}%** din energia lipsă, față de {summary['capture_top20pct_random'] * 100:.0f}% la întâmplare și {summary['capture_top20pct_biggest'] * 100:.0f}% la „posturile mari întâi”.
- Un contor de bilanț montat după clasament găsește în medie ~{lei_year_per_meter:,.0f} lei pe an de energie lipsă (la {price} lei/kWh, `config/economics.yaml`), față de ~{lei_year_random:,.0f} lei pe an la un post ales la întâmplare.
- Clasamentul complet: `reports/bilant/plan_b_ranking.csv`; curbele: `reports/bilant/plan_b.png`.

## Limite

- Furtul înainte de contor nu lasă urme la contoarele clienților. Planul B îl găsește doar prin mărimea și tipul postului, de aceea pierde din ce găsește bilanțul complet.
- Lipsa reală e din construcție (simulare). Pe date PPC, eticheta de antrenare e lipsa măsurată la posturile care au deja contor de bilanț, exact ca aici (`measured_excess`).
"""
    (OUT / "plan_b.md").write_text(md, encoding="utf-8")
    print(tab.to_string(index=False))
    print(json.dumps(summary, indent=1))


def _fig(curves: dict, n: int) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 4.5))
    x = np.arange(1, n + 1) / n * 100
    styles = {"model (planul B)": ("#2b6cb0", 2.2), "posturile mari întâi": ("#dd6b20", 1.3), "pierderea tehnică estimată întâi": ("#805ad5", 1.3), "la întâmplare (media a 200 de trageri)": ("#a0aec0", 1.3)}
    for name, c in curves.items():
        col, lw = styles[name]
        ax.plot(x, c * 100, label=name, color=col, lw=lw)
    ax.axvline(100 - 58.81, color="#444", ls=":", lw=1)
    ax.text(100 - 58.81 + 1, 5, "posturi fără contoare\ninteligente, Muntenia (41%)", fontsize=7)
    ax.set_xlabel("% din posturi cu contor de bilanț montat (în ordinea metodei)")
    ax.set_ylabel("% din energia lipsă găsită")
    ax.set_title("Planul B: unde montăm întâi contoarele de bilanț (SIMULARE)", fontsize=10)
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "plan_b.png", dpi=130)
    plt.close(fig)


if __name__ == "__main__":
    main()
