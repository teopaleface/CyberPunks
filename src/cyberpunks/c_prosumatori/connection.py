"""Cererile noi de racordare ale prosumatorilor: aprobat, aprobat cu limită de injecție sau studiu, cu explicație.

Pentru un post și o cerere (kWp, baterie, locul racordării), modelul C estimează tensiunea maximă înainte și
după racordare, pe zilele de referință (cele mai însorite zile din sezonul 2025) și pe tot anul 2025 (zilele
așteptate cu depășire). Unde rețeaua postului e cunoscută (posturile demo), calculul de rețea confirmă rezultatul
și găsește limita de injecție. Comparația cu regula simplă de azi: creșterea de tensiune la punctul de racord
ΔU ≈ R·P/U² față de pragul de 3% (VDE-AR-N 4105).

    uv run python -m cyberpunks.c_prosumatori.connection --post PT-1047 --kwp 10
    uv run python -m cyberpunks.c_prosumatori.connection --post PT-1047 --kwp 10 --battery 10
"""

from __future__ import annotations

import argparse
import dataclasses
import json

import numpy as np
import pandas as pd

from cyberpunks.c_prosumatori import features as F
from cyberpunks.c_prosumatori import posts, profiles, remedies, simulate, weather
from cyberpunks.c_prosumatori import train as T
from cyberpunks.c_prosumatori.explain import fmt

LIMIT = 1.10
MARGIN = 0.002
REF_DAYS = 15  # zilele de referință: cele mai însorite din aprilie-septembrie 2025
VDE_RULE = 0.03  # VDE-AR-N 4105: creșterea de tensiune la punctul de racord ≤ 3% (regula simplă de comparație)
EXPORT_LIMITS = (0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.0)  # fracții din kWp încercate pentru limita de injecție


def _year_days(year: int = 2025) -> tuple[pd.DataFrame, list]:
    """Vremea orară a anului și cele mai însorite zile din aprilie-septembrie (zilele de referință)."""
    if year not in (2023, 2024, 2025):
        raise ValueError(f"anul {year} nu e complet în arhiva meteo (2023-2025)")
    wx = weather.archive()
    wx = wx[(wx.index >= f"{year}-01-01") & (wx.index < f"{year + 1}-01-01")]
    hw = F.hourly_weather(wx)
    dw = F.daily_weather(hw)
    season = [d for d in dw.index if 4 <= d.month <= 9]
    ref = dw.loc[season].sort_values("pvk_max", ascending=False).head(REF_DAYS).index.tolist()
    return hw, sorted(ref)


def _with_new_pv(post, load_index: int, kwp: float, battery_kwh: float):
    """Postul cu un prosumator nou (aceeași rețea, o injecție în plus la casa aleasă)."""
    bkw = float(np.clip(battery_kwh / 2.0, 2.5, 5.0)) if battery_kwh > 0 else 0.0
    return dataclasses.replace(
        post,
        pv_load=np.r_[post.pv_load, load_index],
        pv_bus=np.r_[post.pv_bus, post.load_bus[load_index]],
        pv_kwp=np.r_[post.pv_kwp, kwp],
        pv_ac_kw=np.r_[post.pv_ac_kw, kwp],
        pv_orient=np.r_[post.pv_orient, 0.92],
        bat_kwh=np.r_[post.bat_kwh, battery_kwh],
        bat_kw=np.r_[post.bat_kw, bkw],
    )


def _static_after(row: pd.Series, post, new_post) -> pd.Series:
    """Trăsăturile statice ale postului după racordare (ce ar ști distribuitorul din cerere și din GIS)."""
    R, pv_lv, _ = remedies._lv_maps(new_post)
    r = row.copy()
    r["pv_kw"] = float(new_post.pv_kwp.sum())
    r["n_prosumers"] = len(new_post.pv_kwp)
    r["pv_kw_per_kva"] = r["pv_kw"] / r["kva"]
    r["prosumer_share"] = r["n_prosumers"] / max(int(post.load_is_house.sum()), 1)
    r["battery_kwh"] = float(new_post.bat_kwh.sum())
    r["battery_pv_share"] = float(new_post.pv_kwp[new_post.bat_kwh > 0].sum() / max(new_post.pv_kwp.sum(), 1e-9))
    r["sens_pv_pu"] = float((R[:, pv_lv] @ (new_post.pv_kwp / 1000)).max())
    return r


def assess(post_id: str, kwp: float, battery_kwh: float = 0.0, load_index: int | None = None) -> dict:
    """Decizia pentru o cerere de racordare. Întoarce un dicționar cu decizia, cifrele și explicația în română."""
    if not (0 < kwp <= 400):
        return {"decision": "respins_intrare", "explanation_ro": f"Puterea cerută ({kwp} kWp) nu e validă pentru un prosumator (0-400 kWp).",
                "rule_id": "C-RAC-0-INTRARE"}
    reg = posts.load_posts().set_index("post_id")
    if post_id not in reg.index:
        return {"decision": "respins_intrare", "explanation_ro": f"Postul {post_id} nu există în registru.", "rule_id": "C-RAC-0-INTRARE"}
    row = reg.loc[post_id].copy()
    row["post_id"] = post_id
    post = posts.build_post(post_id)
    R, _, ld_lv = remedies._lv_maps(post)
    houses = [i for i in np.flatnonzero(post.load_is_house) if i not in set(post.pv_load)]
    if load_index is None:  # cel mai expus punct de racord dintre casele fără panouri (prudent)
        load_index = int(max(houses or range(len(post.load_bus)), key=lambda i: R[ld_lv[i], ld_lv[i]]))
    new_post = _with_new_pv(post, load_index, kwp, battery_kwh)
    after = _static_after(row, post, new_post)
    bundle = T.load_bundle()
    hw, ref = _year_days()

    def model_days(r: pd.Series) -> pd.DataFrame:
        X = F.daily_features(pd.DataFrame([r]), hw)
        p = bundle.daily.predict(X)
        return pd.DataFrame({"date": X["date"], "q50": p["q50"], "q90": p["q90"], "p": p["p_exceed"]})

    before_y, after_y = model_days(row), model_days(after)
    b_ref, a_ref = before_y[before_y.date.isin(ref)], after_y[after_y.date.isin(ref)]
    exp_before, exp_after = float(before_y.p.sum()), float(after_y.p.sum())

    # calculul de rețea pe zilele de referință (rețeaua postului e cunoscută la posturile demo)
    wx = weather.archive()
    loc_date = (wx.index.tz_convert(profiles.TZ) - pd.Timedelta(hours=1)).date
    sel = np.isin(loc_date, ref)
    wx_ref = wx[sel]
    shapes, sysload = profiles.shapes_for(wx_ref.index), profiles.system_load_index(wx_ref.index)

    def phys(p, cap_frac: float | None = None) -> float:
        cap = None if cap_frac is None else np.r_[np.full(len(p.pv_kwp) - 1, np.inf), cap_frac * kwp]
        h = simulate.simulate_post(p, wx_ref, shapes, sysload, export_cap_kw=cap)
        return float(h["vmax"].max())

    v_before, v_after = phys(post), phys(new_post)
    # regula simplă de azi: ΔU la punctul de racord
    du = float(R[ld_lv[load_index], ld_lv[load_index]] * kwp / 1000)
    rule_simple = "aprobat" if du <= VDE_RULE else "studiu"
    p90_before, p90_after = float(b_ref.q90.max()), float(a_ref.q90.max())
    out = {
        "post_id": post_id, "kwp": kwp, "battery_kwh": battery_kwh, "load_index": load_index,
        "p90_ref_before_pu": round(p90_before, 4), "p90_ref_after_pu": round(p90_after, 4),
        "expected_days_over_before": round(exp_before, 1), "expected_days_over_after": round(exp_after, 1),
        "physics_vmax_ref_before_pu": round(v_before, 4), "physics_vmax_ref_after_pu": round(v_after, 4),
        "simple_rule_du_pu": round(du, 4), "simple_rule_decision": rule_simple, "reference_days": [d.isoformat() for d in ref],
        "synthetic": True,
    }
    worst = max(p90_after, v_after)
    if max(p90_before, v_before) >= LIMIT - MARGIN:
        out.update(decision="studiu", rule_id="C-RAC-3-POST-DEJA-PESTE",
                   explanation_ro=(f"Postul {post_id} trece deja de 1,10 pu în zilele însorite (P90 {fmt(p90_before, 3)} pu, calcul de rețea "
                                   f"{fmt(v_before, 3)} pu). Un prosumator nou de {kwp:g} kWp ar urca tensiunea la {fmt(worst, 3)} pu. "
                                   "Întâi soluțiile din scară (faze, priză), apoi racordarea."))
    elif worst < LIMIT - MARGIN and exp_after - exp_before <= 1.0:
        out.update(decision="aprobat", rule_id="C-RAC-1-APROBAT",
                   explanation_ro=(f"Cu {kwp:g} kWp în plus, tensiunea maximă în cele mai însorite {REF_DAYS} zile din 2025 rămâne la "
                                   f"{fmt(worst, 3)} pu, sub 1,10. Zile așteptate cu depășire pe an: {fmt(exp_before, 1)} → {fmt(exp_after, 1)}."))
    else:
        limit = None
        for f in EXPORT_LIMITS:
            if phys(new_post, f) < LIMIT - MARGIN:
                limit = f
                break
        if limit is not None:
            out.update(decision="aprobat_cu_limita", export_limit_kw=round(limit * kwp, 1), rule_id="C-RAC-2-LIMITA",
                       explanation_ro=(f"Fără limită, tensiunea ar urca la {fmt(worst, 3)} pu în zilele însorite. Cu injecția limitată la "
                                       f"{limit * kwp:.1f} kW ({limit:.0%} din {kwp:g} kWp), calculul de rețea rămâne sub 1,10 pu."
                                       + (" O baterie ar reduce energia pierdută prin limitare." if battery_kwh == 0 else "")))
        else:
            out.update(decision="studiu", rule_id="C-RAC-3-STUDIU",
                       explanation_ro=(f"Nici cu injecție zero în orele cu soare tensiunea nu rămâne sub 1,10 pu ({fmt(worst, 3)} pu fără limită). "
                                       "Cererea merge la studiu de soluție (cablu, post nou)."))
    out["explanation_ro"] += (f" Regula simplă de azi (ΔU ≤ 3% la punctul de racord) ar fi dat „{rule_simple}” "
                              f"(ΔU = {fmt(du * 100, 1)}%).")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--post", required=True)
    ap.add_argument("--kwp", type=float, required=True)
    ap.add_argument("--battery", type=float, default=0.0)
    ap.add_argument("--load-index", type=int, default=None)
    a = ap.parse_args()
    print(json.dumps(assess(a.post, a.kwp, a.battery, a.load_index), ensure_ascii=False, indent=2))
