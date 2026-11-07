"""Verificarea de realism: curbele zilnice ale posturilor simulate față de posturi reale din UK (Weave).

Sursa: Centre for AI and Climate, „UK LV Feeder Smart Meter Data” (Weave), consumul contoarelor inteligente însumat pe
post, la 30 de minute: https://github.com/centre-for-ai-and-climate/lv-feeder-smart-meter-data (mostra pentru
2024-02-12, `2024-02-12-aggregated-by-substation.csv.gz`, ~38 MB). Licența nu e declarată, deci o folosim doar ca reper
pentru forma curbelor, citat, nu ca etichete și nu în antrenare. Fișierul stă în `data/raw/bilant/weave/` (în afara git).

Limită: în UK nu toți clienții au contor inteligent, deci suma nu acoperă tot postul. Comparăm forma curbei (normată),
nu nivelul.

    uv run python -m cyberpunks.a_bilant.weave_check      # scrie reports/bilant/weave_check.md și weave_check.png
"""

from __future__ import annotations

import json
from functools import cache

import numpy as np
import pandas as pd

from cyberpunks.a_bilant import world
from cyberpunks.common.paths import DATA_PROCESSED, DATA_RAW, REPORTS

URL = "https://raw.githubusercontent.com/centre-for-ai-and-climate/lv-feeder-smart-meter-data/main/2024-02-12-aggregated-by-substation.csv.gz"
RAW = DATA_RAW / "bilant" / "weave" / "2024-02-12-aggregated-by-substation.csv.gz"
SIM_DAY = "2025-02-10"  # tot luni, în februarie, ca ziua din Weave (2024-02-12)
OUT = REPORTS / "bilant"


def download() -> None:
    if RAW.exists():
        return
    import httpx

    RAW.parent.mkdir(parents=True, exist_ok=True)
    with httpx.stream("GET", URL, follow_redirects=True, timeout=120, headers={"User-Agent": "CyberPunks-hackathon/0.1"}) as r:
        r.raise_for_status()
        with open(RAW, "wb") as f:
            f.writelines(r.iter_bytes())


def shape_metrics(curves: np.ndarray) -> pd.DataFrame:
    """Curbe orare (n, 24), consum pozitiv: factorul de încărcare, ponderea nopții (00-06), ora vârfului, raportul seară/zi."""
    c = np.clip(curves, 0, None)
    tot = c.sum(1)
    ok = tot > 0
    c, tot = c[ok], tot[ok]
    return pd.DataFrame(
        {
            "factor_incarcare": c.mean(1) / c.max(1),
            "pondere_noapte": c[:, 0:6].sum(1) / tot,
            "ora_varf": c.argmax(1),
            # numitorul are o limită jos (20% din media zilei): la prosumatori, consumul net la prânz poate fi ~0
            "seara_fata_de_zi": c[:, 17:21].mean(1) / np.maximum(c[:, 10:14].mean(1), 0.2 * c.mean(1)),
        }
    )


@cache
def weave_curves() -> np.ndarray:
    download()
    d = pd.read_csv(RAW, usecols=["substation", "consumption", "timestamp"])
    ts = pd.to_datetime(d["timestamp"])
    # eticheta e sfârșitul intervalului de 30 de minute (00:30 = 00:00-00:30); ora începutului
    d["hour"] = ((ts - pd.Timedelta(minutes=30)).dt.hour).astype(int)
    d = d[(ts - pd.Timedelta(minutes=30)).dt.date.astype(str) == "2024-02-12"]
    piv = d.groupby(["substation", "hour"])["consumption"].sum().unstack()
    return piv.dropna().to_numpy(dtype=float)


@cache
def sim_curves(pool: str = "pop") -> np.ndarray:
    wx = world.load_weather()
    day = int(wx.days.get_loc(pd.Timestamp(SIM_DAY)))
    hrs = np.flatnonzero(wx.local_day == day)
    h = np.load(DATA_PROCESSED / "bilant" / pool / "hourly.npz")
    out = []
    for k in h.files:
        if k.startswith("db__"):
            x = h[k][hrs].astype(float)
            if len(x) == 24:
                # consumul fără injecția prosumatorilor nu se poate separa din net; în februarie injecția e mică
                out.append(x)
    return np.array(out)


def main() -> None:
    w = shape_metrics(weave_curves())
    s = shape_metrics(sim_curves())
    rows = []
    for col, name in (("factor_incarcare", "factorul de încărcare (medie / vârf)"), ("pondere_noapte", "ponderea nopții 00-06 în consumul zilei"), ("seara_fata_de_zi", "seara 17-21 față de prânz 10-14")):
        rows.append({"măsura": name, "Weave UK (mediană, P10-P90)": f"{w[col].median():.2f} ({w[col].quantile(0.1):.2f}-{w[col].quantile(0.9):.2f})", "simulare (mediană, P10-P90)": f"{s[col].median():.2f} ({s[col].quantile(0.1):.2f}-{s[col].quantile(0.9):.2f})"})
    peak_w = w["ora_varf"].value_counts(normalize=True).sort_index()
    peak_s = s["ora_varf"].value_counts(normalize=True).sort_index()
    summary = {
        "weave_posts": len(w),
        "sim_posts": len(s),
        **{f"{c}_weave_median": float(w[c].median()) for c in ("factor_incarcare", "pondere_noapte", "seara_fata_de_zi")},
        **{f"{c}_sim_median": float(s[c].median()) for c in ("factor_incarcare", "pondere_noapte", "seara_fata_de_zi")},
        "peak_hour_mode_weave": int(peak_w.idxmax()),
        "peak_hour_mode_sim": int(peak_s.idxmax()),
    }
    (OUT / "weave_check.json").write_text(json.dumps(summary, indent=2))
    _fig(weave_curves(), sim_curves())
    cols = list(rows[0])
    tab = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)] + ["| " + " | ".join(r[c] for c in cols) + " |" for r in rows]
    md = [
        "# Verificarea de realism: curbele posturilor simulate față de posturi reale (Weave, UK)",
        "",
        "Sursa reală: Centre for AI and Climate, Weave, consumul contoarelor inteligente însumat pe post la 30 de minute, 2024-02-12 (luni), https://github.com/centre-for-ai-and-climate/lv-feeder-smart-meter-data. Licența nu e declarată: îl folosim doar ca reper pentru forma curbelor, nu ca etichete și nu la antrenare. Comanda: `uv run python -m cyberpunks.a_bilant.weave_check`.",
        "",
        f"Comparăm {len(w)} de posturi reale cu cele {len(s)} de posturi simulate ale hărții, pe o zi de luni din februarie ({SIM_DAY}), după forma curbei (normată), nu după nivel: în UK nu toți clienții au contor inteligent.",
        "",
        *tab,
        "",
        f"- Ora de vârf cea mai frecventă: {summary['peak_hour_mode_weave']}:00 în datele reale, {summary['peak_hour_mode_sim']}:00 în simulare.",
        "- Figura: `reports/bilant/weave_check.png` (curbele medii normate, cu banda P10-P90).",
        "- Raportul seară/prânz e mai mare în simulare: posturile simulate au mulți prosumatori (Ilfov e primul județ la prosumatori), iar contorul net arată la prânz consumul minus producția panourilor; în datele UK, contorul dă consumul. Numitorul are o limită jos (20% din media zilei).",
        "- Concluzie: simularea e un reper, nu o copie. Profilele SimBench (germane) și consumul românesc diferă de UK, iar diferențele de mai sus spun cât. Modelul învață din formă și din încărcare, deci contează mai ales ca forma să fie plauzibilă. Pe date PPC, curbele vin direct din contoare.",
        "",
    ]
    (OUT / "weave_check.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))


def _fig(wc: np.ndarray, sc: np.ndarray) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    def norm(c: np.ndarray) -> np.ndarray:
        c = np.clip(c, 0, None)
        c = c[c.sum(1) > 0]
        return c / c.mean(1, keepdims=True)

    fig, ax = plt.subplots(figsize=(7.5, 4))
    for c, lab, col in ((norm(wc), "posturi reale UK (Weave, 12 feb. 2024)", "#dd6b20"), (norm(sc), "posturi simulate, harta (10 feb. 2025)", "#2b6cb0")):
        x = np.arange(24) + 0.5
        ax.fill_between(x, np.quantile(c, 0.1, 0), np.quantile(c, 0.9, 0), color=col, alpha=0.15)
        ax.plot(x, np.median(c, 0), color=col, lw=2, label=lab)
    ax.set_xlabel("ora")
    ax.set_ylabel("consum / media zilei")
    ax.set_xticks(range(0, 25, 3))
    ax.legend(fontsize=8)
    ax.set_title("Forma zilnică a consumului pe post: real (UK) față de simulat", fontsize=10)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "weave_check.png", dpi=130)
    plt.close(fig)


if __name__ == "__main__":
    main()
