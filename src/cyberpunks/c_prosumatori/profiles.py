"""Profilele de consum SimBench (2016, la 15 minute), mutate pe calendarul românesc, la oră.

Fiecare profil devine o formă orară normată (suma pe 2016 = 1); consumul unui client la ora t este
consum_anual × formă(t). O zi țintă se leagă de o zi din 2016 cu aceeași zi a săptămânii și aceeași
perioadă din an. Sărbătorile legale românești se tratează ca duminici.
"""

from __future__ import annotations

from datetime import date, timedelta
from functools import cache

import numpy as np
import pandas as pd

from cyberpunks.common.paths import DATA_INTERIM

TZ = "Europe/Bucharest"
CACHE = DATA_INTERIM / "C" / "simbench_load_profiles_hourly.parquet"

# Paștele ortodox (sursa: calendarul BOR); Vinerea Mare, Paștele, a doua zi, Rusaliile și a doua zi sunt libere.
ORTHODOX_EASTER = {2023: date(2023, 4, 16), 2024: date(2024, 5, 5), 2025: date(2025, 4, 20), 2026: date(2026, 4, 12), 2027: date(2027, 5, 2)}
FIXED_HOLIDAYS = [(1, 1), (1, 2), (1, 6), (1, 7), (1, 24), (5, 1), (6, 1), (8, 15), (11, 30), (12, 1), (12, 25), (12, 26)]


@cache
def holidays(year: int) -> frozenset[date]:
    days = {date(year, m, d) for m, d in FIXED_HOLIDAYS}
    e = ORTHODOX_EASTER.get(year)
    if e:
        days |= {e - timedelta(days=2), e, e + timedelta(days=1), e + timedelta(days=49), e + timedelta(days=50)}
    return frozenset(days)


def is_free_day(d: date) -> bool:
    return d.weekday() >= 5 or d in holidays(d.year)


@cache
def hourly_shapes() -> pd.DataFrame:
    """Formele orare (8784 ore din 2016) pentru toate profilele de consum din cele 6 rețele SimBench."""
    if CACHE.exists():
        return pd.read_parquet(CACHE)
    import simbench as sb

    from cyberpunks.c_prosumatori.grids import TOPOLOGIES

    frames = {}
    for code in TOPOLOGIES.values():
        lp = sb.get_simbench_net(code).profiles["load"]
        for col in lp.columns:
            if col.endswith("_pload"):
                frames[col.removesuffix("_pload")] = lp[col].to_numpy(dtype=float)
    q = pd.DataFrame(frames)
    # 4 sferturi de oră -> o oră; eticheta e ora care se încheie (convenția Open-Meteo)
    hourly = q.groupby(np.arange(len(q)) // 4).mean()
    hourly = hourly / hourly.sum()
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    hourly.to_parquet(CACHE)
    return hourly


def _map_day_to_2016(d: date) -> int:
    """Indexul zilei din 2016 (0..365) cu aceeași zi a săptămânii, cât mai aproape de aceeași dată."""
    try:
        ref = date(2016, d.month, d.day)
    except ValueError:  # 29 februarie
        ref = date(2016, 2, 28)
    target_wd = 6 if is_free_day(d) else d.weekday()
    if target_wd == 6 and d.weekday() == 5:
        target_wd = 5  # sâmbăta rămâne sâmbătă
    best = None
    for k in range(-3, 4):
        c = ref + timedelta(days=k)
        if c.year != 2016:
            continue
        if c.weekday() == target_wd and (best is None or abs(k) < abs(best[0])):
            best = (k, c)
    c = best[1] if best else ref
    return (c - date(2016, 1, 1)).days


def shapes_for(times_utc: pd.DatetimeIndex) -> pd.DataFrame:
    """Forma orară a fiecărui profil pentru orele date (UTC, ora care se încheie)."""
    loc = times_utc.tz_convert(TZ)
    start = loc - pd.Timedelta(hours=1)  # începutul orei, în ora locală
    days = np.array([_map_day_to_2016(d) for d in start.date])
    idx = np.clip(days * 24 + start.hour.to_numpy(), 0, 8783)
    sh = hourly_shapes()
    out = sh.iloc[idx].reset_index(drop=True)
    out.index = times_utc
    return out


def system_load_index(times_utc: pd.DatetimeIndex) -> np.ndarray:
    """Un indice 0..1 al consumului casnic total (media profilelor H0), pentru variația tensiunii pe MT."""
    sh = shapes_for(times_utc)
    h0 = sh[[c for c in sh.columns if c.startswith("H0")]].mean(axis=1).to_numpy()
    return h0 / np.max(hourly_shapes()[[c for c in sh.columns if c.startswith("H0")]].mean(axis=1).to_numpy())
