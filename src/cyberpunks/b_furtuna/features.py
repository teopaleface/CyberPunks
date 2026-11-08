"""Variabilele (features) modelului B. Aceeași funcție servește la antrenare (comitate SUA) și la aplicare
(zone România), ca să nu apară diferențe între cele două.

Intrarea: un tabel zilnic pe locație cu variabilele Open-Meteo din `openmeteo.DAILY_VARS`, plus
`customers` și `area_km2` ale zonei. Ieșirea: coloanele din `FEATURES`.

Codul meteo (`weather_code`) NU intră în model: arhiva nu are niciodată coduri de furtună (95-99),
prognoza le are, deci ar fi o diferență între antrenare și producție. Nici temperaturile: vezi FEATURE_SPEC.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# (coloană, constrângere monotonă pentru LightGBM: +1 = riscul nu scade când valoarea crește)
FEATURE_SPEC: list[tuple[str, int]] = [
    ("gust_max", 1),  # rafala maximă a zilei, km/h
    ("wind_max", 1),  # vântul mediu maxim, km/h
    ("gust_prev", 1),  # rafala maximă din ziua precedentă (avarii rămase din ajun)
    ("gust_max_2d", 1),  # max(azi, ieri)
    ("precip", 1),  # ploaie + ninsoare azi, mm
    ("precip_48h", 1),  # azi + ieri, mm
    ("precip_7d", 1),  # ultimele 7 zile, mm: sol îmbibat, copaci smulși mai ușor
    ("precip_hours", 0),
    ("snow", 1),  # ninsoare azi, cm
    ("snow_3d", 1),  # ninsoare în 3 zile, cm
    ("ice_proxy", 1),  # ploaie (mm) într-o zi cu minima sub 0,5 °C: risc de chiciură sau polei
    # Temperaturile și radiația (tmax, tmin, t_range, srad) au fost scoase la 13:55: pe testul din SUA aduceau ~3% PR-AUC,
    # dar în România trimiteau echipe la caniculă (verile de acolo sunt mai calde decât ce a văzut modelul).
    # Le păstrăm calculate mai jos pentru experimente (`experiments.py`, varianta „cu_temperaturi”).
    ("doy_sin", 0),  # sezonul (frunzișul)
    ("doy_cos", 0),
    ("log_customers", 0),  # mărimea zonei
    ("log_density", 0),  # clienți pe km²: urban față de rural
]
FEATURES = [f for f, _ in FEATURE_SPEC]
MONOTONE = [m for _, m in FEATURE_SPEC]

# Limitele fizice acceptate la intrare (dincolo de ele valoarea e considerată greșită)
VALID_RANGES = {
    "wind_gusts_10m_max": (0.0, 250.0),
    "wind_speed_10m_max": (0.0, 200.0),
    "precipitation_sum": (0.0, 500.0),
    "rain_sum": (0.0, 500.0),
    "snowfall_sum": (0.0, 200.0),
    "precipitation_hours": (0.0, 24.0),
    "temperature_2m_max": (-50.0, 55.0),
    "temperature_2m_min": (-60.0, 45.0),
    "shortwave_radiation_sum": (0.0, 40.0),
}


def clean_weather(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Înlocuiește valorile imposibile cu NaN și întoarce lista problemelor găsite (în română)."""
    df = df.copy()
    issues: list[str] = []
    for col, (lo, hi) in VALID_RANGES.items():
        if col not in df:
            continue
        bad = (df[col] < lo) | (df[col] > hi)
        if bad.any():
            issues.append(f"{int(bad.sum())} valori imposibile în {col} (în afara [{lo}, {hi}]): înlocuite cu lipsă")
            df.loc[bad, col] = np.nan
    if {"temperature_2m_max", "temperature_2m_min"} <= set(df):
        swapped = df["temperature_2m_min"] > df["temperature_2m_max"] + 0.5
        if swapped.any():
            issues.append(f"{int(swapped.sum())} zile cu minima peste maxima: valori inversate")
            lo, hi = df.loc[swapped, "temperature_2m_max"].copy(), df.loc[swapped, "temperature_2m_min"].copy()
            df.loc[swapped, "temperature_2m_min"], df.loc[swapped, "temperature_2m_max"] = lo, hi
    return df, issues


def make_features(df: pd.DataFrame, group: str = "loc_id") -> pd.DataFrame:
    """Adaugă coloanele din FEATURES. `df` are câte un rând pe (locație, zi), cu coloana `date`."""
    df = df.sort_values([group, "date"]).copy()
    g = df.groupby(group, sort=False)
    df["gust_max"] = df["wind_gusts_10m_max"]
    df["wind_max"] = df["wind_speed_10m_max"]
    df["gust_prev"] = g["wind_gusts_10m_max"].shift(1)
    df["gust_max_2d"] = df[["gust_max", "gust_prev"]].max(axis=1)
    df["precip"] = df["precipitation_sum"]
    prev_precip = g["precipitation_sum"].shift(1)
    df["precip_48h"] = df["precip"] + prev_precip
    df["precip_7d"] = g["precipitation_sum"].transform(lambda s: s.rolling(7, min_periods=4).sum())
    df["precip_hours"] = df["precipitation_hours"]
    df["snow"] = df["snowfall_sum"]
    df["snow_3d"] = g["snowfall_sum"].transform(lambda s: s.rolling(3, min_periods=2).sum())
    df["ice_proxy"] = np.where(df["temperature_2m_min"] <= 0.5, df["rain_sum"], 0.0)
    df.loc[df["temperature_2m_min"].isna() | df["rain_sum"].isna(), "ice_proxy"] = np.nan
    df["tmax"] = df["temperature_2m_max"]
    df["tmin"] = df["temperature_2m_min"]
    df["t_range"] = df["tmax"] - df["tmin"]
    df["srad"] = df["shortwave_radiation_sum"]
    doy = pd.to_datetime(df["date"]).dt.dayofyear
    df["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    df["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    df["log_customers"] = np.log10(df["customers"].clip(lower=1))
    df["log_density"] = np.log10((df["customers"] / df["area_km2"]).clip(lower=0.01))
    return df


# Cum se spune fiecare factor în cuvinte simple (pentru explicații). {v} = valoarea.
LABELS_RO = {
    "gust_max": "rafale de vânt de {v:.0f} km/h",
    "wind_max": "vânt susținut de {v:.0f} km/h",
    "gust_prev": "rafale de {v:.0f} km/h în ziua de dinainte",
    "gust_max_2d": "rafale de până la {v:.0f} km/h în ultimele 2 zile",
    "precip": "{v:.0f} mm de ploaie în ziua respectivă",
    "precip_48h": "{v:.0f} mm de ploaie în 48 de ore",
    "precip_7d": "{v:.0f} mm de ploaie în 7 zile (sol îmbibat)",
    "precip_hours": "{v:.0f} ore cu precipitații",
    "snow": "{v:.0f} cm de zăpadă nouă",
    "snow_3d": "{v:.0f} cm de zăpadă în 3 zile",
    "ice_proxy": "{v:.0f} mm de ploaie la temperaturi sub 0 °C (risc de polei)",
    "tmax": "maxima de {v:.0f} °C",
    "tmin": "minima de {v:.0f} °C",
    "t_range": "diferență de {v:.0f} °C între zi și noapte",
    "srad": "radiație solară puternică ({v:.0f} MJ/m²), aer instabil",
    "doy_sin": "sezonul (frunziș, furtuni de vară)",
    "doy_cos": "sezonul (frunziș, furtuni de vară)",
    "log_customers": "mărimea zonei ({v:.0f} clienți)",
    "log_density": "densitatea rețelei ({v:.0f} clienți/km²)",
}


def label_ro(feature: str, row: pd.Series) -> tuple[str, float | str | None]:
    """Textul și valoarea afișată pentru un factor."""
    if feature == "log_customers":
        v = float(row["customers"])
    elif feature == "log_density":
        v = float(row["customers"] / row["area_km2"])
    else:
        v = row.get(feature)
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return f"{feature}: lipsă", None
    if feature == "log_customers":
        return f"mărimea zonei ({round(v):,} clienți)".replace(",", "."), round(float(v), 2)
    return LABELS_RO.get(feature, feature + " {v}").format(v=float(v)), round(float(v), 2)
