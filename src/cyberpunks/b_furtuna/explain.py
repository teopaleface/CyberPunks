"""Explicațiile modelului B: factorii (SHAP), zilele istorice asemănătoare și fraza din șablon.

Cifrele din frază vin din cod (vremea și predicția), nu dintr-un LLM.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from cyberpunks.b_furtuna.features import label_ro
from cyberpunks.b_furtuna.model import CASE_FEATURES, BModel, shap_values
from cyberpunks.common.contracts import Factor, SimilarCase


def top_factors(model: BModel, rows: pd.DataFrame, k: int = 4) -> list[list[Factor]]:
    """Pentru fiecare rând, cei mai importanți k factori (contribuția SHAP în log-odds)."""
    sv = shap_values(model, rows)[:, :-1]
    feats = model.features
    out = []
    for i, (_, row) in enumerate(rows.iterrows()):
        contrib = dict(zip(feats, sv[i], strict=True))
        season = contrib.pop("doy_sin", 0.0) + contrib.pop("doy_cos", 0.0)
        # gust_max_2d dublează gust_max / gust_prev: îl adunăm la rafala cea mai mare dintre cele două
        g2 = contrib.pop("gust_max_2d", 0.0)
        key = "gust_max" if (row.get("gust_max") or 0) >= (row.get("gust_prev") or 0) else "gust_prev"
        contrib[key] = contrib.get(key, 0.0) + g2
        ranked = sorted(contrib.items(), key=lambda kv: kv[1], reverse=True)
        positive = [(f, c) for f, c in ranked if c > 0.01]
        chosen = positive[:k] if positive else sorted(contrib.items(), key=lambda kv: abs(kv[1]), reverse=True)[:k]
        factors = []
        for f, c in chosen:
            text, val = label_ro(f, row)
            factors.append(Factor(feature=f, label_ro=text, value=val, contribution=round(float(c), 4)))
        if abs(season) > 0.05 and len(factors) < 8:
            month = pd.Timestamp(row["date"]).month
            text = "sezonul de vară: frunziș bogat, furtuni convective" if month in (5, 6, 7, 8, 9) else (
                "sezonul rece: gheață și zăpadă posibile" if month in (12, 1, 2, 3) else "sezonul de tranziție")
            factors.append(Factor(feature="season", label_ro=text, value=month, contribution=round(float(season), 4)))
        out.append(factors)
    return out


def similar_cases(model: BModel, rows: pd.DataFrame, k: int = 3) -> list[list[SimilarCase]]:
    """Zilele istorice (comitate SUA) cu vremea cea mai apropiată, și ce s-a întâmplat atunci."""
    lib = model.cases
    if lib is None or lib.empty:
        return [[] for _ in range(len(rows))]
    mu = np.array([model.case_scale[f][0] for f in CASE_FEATURES])
    sd = np.array([model.case_scale[f][1] for f in CASE_FEATURES])
    L = (lib[CASE_FEATURES].to_numpy(dtype=float) - mu) / sd
    L = np.nan_to_num(L)
    w = np.array([2.0, 1.0, 1.5, 0.7, 1.0, 1.0, 0.7, 0.5, 0.7, 0.7])  # rafala și ploaia contează cel mai mult
    out = []
    for _, row in rows.iterrows():
        x = np.nan_to_num((row[CASE_FEATURES].to_numpy(dtype=float) - mu) / sd)
        d = np.sqrt((((L - x) ** 2) * w).sum(axis=1) / w.sum())
        idx = np.argsort(d)[:k]
        cases = []
        for j in idx:
            c = lib.iloc[j]
            pct = float(c["pct_out_max"])
            outcome = "avarii_extinse" if pct >= 0.05 else ("avarii" if c["event"] == 1 else "fara_avarii_semnificative")
            day = pd.Timestamp(c["date"]).date().isoformat()
            cases.append(
                SimilarCase(
                    case_id=f"EAGLEI-{c['state']}-{c['fips']}-{day}",
                    outcome=outcome,
                    similarity=round(float(1.0 / (1.0 + d[j])), 3),
                    note_ro=(f"{c['county']} ({c['state']}, SUA), {day}: vârf {pct:.1%} din clienți fără curent; "
                             f"rafale {c['gust_max']:.0f} km/h, {c['precip_48h']:.0f} mm în 48 h"),
                )
            )
        out.append(cases)
    return out


def summary_ro(p: float, row: pd.Series, onset_hour: int | None, cases: list[SimilarCase], abstain: bool,
               customers_p50: int) -> str:
    g = row.get("gust_max")
    parts = [f"Risc de {p:.0%} ca peste 1% din clienții zonei să rămână fără curent."]
    if g is not None and not np.isnan(g):
        when = f" în jurul orei {onset_hour}:00" if onset_hour is not None else ""
        parts.append(f"Rafale de până la {g:.0f} km/h{when}, {row.get('precip_48h', 0):.0f} mm de ploaie în 48 de ore.")
    if p >= 0.15:
        parts.append(f"Dacă se produce, estimăm circa {customers_p50:,} clienți afectați la vârf.".replace(",", "."))
    if cases:
        bad = sum(c.outcome != "fara_avarii_semnificative" for c in cases)
        parts.append(f"În {bad} din {len(cases)} zile asemănătoare din istoric au fost avarii.")
    if abstain:
        parts.append("Nu sunt sigur: decide dispecerul.")
    return " ".join(parts)
