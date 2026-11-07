"""Trăsăturile modelului: ce știe distribuitorul despre post (GIS, avize de racordare) plus prognoza meteo.

Modelul nu vede rețeaua detaliată și nici consumul real al fiecărei case. Vede:
- postul: kVA, câți clienți și prosumatori, kW instalați, baterii, lungimea și rezistența rețelei, priza,
  tensiunea estimată pe MT, sensibilitatea liniară a tensiunii la PV și la consum (din topologie);
- vremea: radiația pe panou (GTI), radiația globală, partea difuză, temperatura, norii;
- calendarul: ora, ziua din an, zi liberă sau lucrătoare;
- estimări fizice simple: producția PV estimată, consumul estimat din profilul standard, creșterea liniară
  a tensiunii (ΔU ≈ R·P).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from cyberpunks.c_prosumatori import profiles, weather

STATIC = [
    "kva",
    "n_customers",
    "n_prosumers",
    "pv_kw",
    "pv_kw_per_kva",
    "prosumer_share",
    "battery_kwh",
    "battery_pv_share",
    "annual_load_mwh",
    "line_km",
    "max_path_km",
    "r_max_ohm",
    "sens_pv_pu",
    "sens_load_pu",
    "vk_percent",
    "tap_pos",
    "v0_est",
]
DAILY_WEATHER = ["gti_max", "gti_sum", "ghi_max", "pvk_max", "temp_noon", "cloud_mean", "dif_frac_noon", "free_day", "doy_sin", "doy_cos"]
DAILY_DERIVED = ["net_kw_per_kva_max", "dv_lin_max", "v_lin_max", "load_ratio_noon"]
DAILY_FEATURES = STATIC + DAILY_WEATHER + DAILY_DERIVED
HOURLY_WEATHER = ["gti", "ghi", "dif_frac", "temp", "cloud", "pvk", "hour", "free_day", "doy_sin", "doy_cos"]
HOURLY_DERIVED = ["net_kw_per_kva", "dv_lin", "v_lin", "load_ratio"]
HOURLY_FEATURES = STATIC + HOURLY_WEATHER + HOURLY_DERIVED

ORIENT_MEAN = 0.92  # factorul mediu de orientare a panourilor (vezi grids.ORIENT)
NOON_WINDOW = (10, 16)  # orele locale (început de oră) în care se calculează valorile „de prânz”

FEATURE_LABELS_RO = {
    "kva": "puterea transformatorului (kVA)",
    "n_customers": "clienți pe post",
    "n_prosumers": "prosumatori pe post",
    "pv_kw": "kW de panouri instalați",
    "pv_kw_per_kva": "kW de panouri pe kVA de transformator",
    "prosumer_share": "partea caselor cu panouri",
    "battery_kwh": "kWh de baterii",
    "battery_pv_share": "partea panourilor cu baterie",
    "annual_load_mwh": "consumul anual al postului (MWh)",
    "line_km": "lungimea rețelei (km)",
    "max_path_km": "cel mai lung drum de la post (km)",
    "r_max_ohm": "rezistența până la capătul rețelei (ohm)",
    "sens_pv_pu": "cât ridică panourile tensiunea, din topologie",
    "sens_load_pu": "cât coboară consumul tensiunea, din topologie",
    "vk_percent": "impedanța transformatorului (%)",
    "tap_pos": "priza transformatorului",
    "v0_est": "tensiunea fără sarcină estimată (pu)",
    "gti_max": "radiația maximă pe panou (W/m²)",
    "gti_sum": "radiația pe panou în toată ziua (kWh/m²)",
    "ghi_max": "radiația globală maximă (W/m²)",
    "pvk_max": "producția maximă pe kWp",
    "temp_noon": "temperatura la prânz (°C)",
    "cloud_mean": "nori la prânz (%)",
    "dif_frac_noon": "partea difuză a radiației la prânz",
    "free_day": "zi liberă (weekend sau sărbătoare)",
    "doy_sin": "perioada din an",
    "doy_cos": "perioada din an",
    "net_kw_per_kva_max": "injecția netă estimată pe kVA la prânz",
    "dv_lin_max": "creșterea de tensiune estimată liniar (pu)",
    "v_lin_max": "tensiunea estimată liniar (pu)",
    "load_ratio_noon": "consumul la prânz față de medie",
    "gti": "radiația pe panou (W/m²)",
    "ghi": "radiația globală (W/m²)",
    "dif_frac": "partea difuză a radiației",
    "temp": "temperatura (°C)",
    "cloud": "nori (%)",
    "pvk": "producția pe kWp",
    "hour": "ora",
    "net_kw_per_kva": "injecția netă estimată pe kVA",
    "dv_lin": "creșterea de tensiune estimată liniar (pu)",
    "v_lin": "tensiunea estimată liniar (pu)",
    "load_ratio": "consumul față de medie",
}


def hourly_weather(wx: pd.DataFrame) -> pd.DataFrame:
    """Trăsăturile meteo și de calendar pe oră (aceleași pentru toate posturile). Index UTC."""
    loc_start = wx.index.tz_convert(profiles.TZ) - pd.Timedelta(hours=1)
    sh = profiles.shapes_for(wx.index)
    h0 = sh[[c for c in sh.columns if c.startswith("H0")]].mean(axis=1).to_numpy()
    mean_h0 = 1.0 / 8784  # formele sunt normate la suma 1 pe 2016
    ghi = wx["ghi"].to_numpy(dtype=float)
    doy = loc_start.dayofyear.to_numpy()
    df = pd.DataFrame(
        {
            "gti": wx["gti"].to_numpy(dtype=float),
            "ghi": ghi,
            "dif_frac": np.where(ghi > 5, np.clip(wx["dif"].to_numpy(dtype=float) / np.maximum(ghi, 1e-6), 0, 1), 1.0),
            "temp": wx["temp"].to_numpy(dtype=float),
            "cloud": wx["cloud"].to_numpy(dtype=float),
            "pvk": weather.pv_per_kwp(wx["gti"].to_numpy(), wx["temp"].to_numpy()),
            "hour": loc_start.hour.to_numpy(),
            "free_day": np.array([profiles.is_free_day(d) for d in loc_start.date], dtype=float),
            "doy_sin": np.sin(2 * np.pi * doy / 365.25),
            "doy_cos": np.cos(2 * np.pi * doy / 365.25),
            "load_ratio": h0 / mean_h0,
            "date": loc_start.date,
        },
        index=wx.index,
    )
    return df


def _derived(st: pd.Series | dict, hw: pd.DataFrame) -> dict[str, np.ndarray]:
    pvk, ratio = hw["pvk"].to_numpy(), hw["load_ratio"].to_numpy()
    est_pv = st["pv_kw"] * pvk * ORIENT_MEAN
    est_load = st["annual_load_mwh"] * 1000 / 8760 * ratio
    dv = st["sens_pv_pu"] * pvk * ORIENT_MEAN - st["sens_load_pu"] * ratio
    return {"net_kw_per_kva": (est_pv - est_load) / st["kva"], "dv_lin": dv, "v_lin": st["v0_est"] + dv}


def daily_weather(hw: pd.DataFrame) -> pd.DataFrame:
    """Agregarea pe zi locală a vremii (o singură dată pentru toate posturile)."""
    noon = hw[(hw.hour >= NOON_WINDOW[0]) & (hw.hour < NOON_WINDOW[1])]
    g, gn = hw.groupby("date"), noon.groupby("date")
    pos = np.arange(len(hw))
    pos_max = pd.Series(hw["pvk"].to_numpy(), index=pos).groupby(hw["date"].to_numpy()).idxmax()
    at_max = hw.iloc[pos_max.to_numpy()].set_index("date")
    d = pd.DataFrame(
        {
            "gti_max": g["gti"].max(),
            "gti_sum": g["gti"].sum() / 1000,
            "ghi_max": g["ghi"].max(),
            "pvk_max": g["pvk"].max(),
            "temp_noon": at_max["temp"],
            "cloud_mean": gn["cloud"].mean(),
            "dif_frac_noon": gn["dif_frac"].mean(),
            "free_day": g["free_day"].first(),
            "doy_sin": g["doy_sin"].first(),
            "doy_cos": g["doy_cos"].first(),
            "load_ratio_noon": at_max["load_ratio"],
        }
    )
    d.index.name = "date"
    full = g.size() >= 20  # zilele de la capetele perioadei au doar câteva ore
    return d[full]


def daily_features(posts: pd.DataFrame, hw: pd.DataFrame) -> pd.DataFrame:
    """Un rând pe (post, zi): trăsăturile statice, vremea zilei și estimările fizice maxime ale zilei."""
    dw = daily_weather(hw)
    dates = hw["date"].to_numpy()
    codes, uniq = pd.factorize(dates, sort=True)
    starts = np.flatnonzero(np.r_[True, codes[1:] != codes[:-1]])
    frames = []
    for _, st in posts.iterrows():
        der = _derived(st, hw)
        out = {k + "_max": np.maximum.reduceat(v, starts) for k, v in der.items()}
        f = pd.DataFrame({"net_kw_per_kva_max": out["net_kw_per_kva_max"], "dv_lin_max": out["dv_lin_max"], "v_lin_max": out["v_lin_max"]})
        f["date"] = uniq[codes[starts]]
        f["post_id"] = st["post_id"]
        frames.append(f)
    der = pd.concat(frames, ignore_index=True)
    out = der.merge(dw.reset_index(), on="date", how="inner").merge(posts[["post_id", *STATIC]], on="post_id", how="left")
    return out


def hourly_features(st: pd.Series | dict, hw: pd.DataFrame) -> pd.DataFrame:
    """Trăsăturile orare pentru un post (pentru modelul orar și pentru seria din grafic)."""
    der = _derived(st, hw)
    df = hw[HOURLY_WEATHER].copy()
    df["load_ratio"] = hw["load_ratio"].to_numpy()
    for k, v in der.items():
        df[k] = v
    for k in STATIC:
        df[k] = st[k]
    return df
