"""Validarea intrărilor (robustețe): ce face agentul cu date greșite, lipsă sau prea puține.

Două niveluri:
- `readings_to_halfhours(df)`: citiri brute (timestamp, kWh) -> tablou (zile × 48), cu tratarea orei de vară,
  a timestamp-urilor dublate, a valorilor nenumerice și a unităților greșite;
- `check_window(hh)`: verificări pe fereastra unui contor (zile × 48) înainte de scorare. Întoarce fereastra
  curățată, lista problemelor găsite (cu ce am făcut) și, dacă e cazul, motivul pentru "nu sunt sigur".

Regula: ce se poate repara sigur se repară și se notează (Wh -> kWh, duplicate); ce poate fi chiar defectul
căutat (negative, salturi) se păstrează pentru model și se notează; ce lasă modelul fără date (istoric scurt)
duce la `abstain=True`, cu motivul scris, iar cazul ajunge la un om.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

MAX_KWH_PER_HALFHOUR = 15.0  # 30 kW timp de 30 de minute: peste puterea oricărui branșament casnic
WH_SUSPECT_DAILY_KWH = 300.0  # o locuință nu consumă 300 kWh pe zi; mediana peste prag = valori în Wh
MIN_VALID_DAYS = 60  # sub atâtea zile cu date, modelul nu are istoric cu care să compare
MIN_RECENT_DAYS = 7  # zile cu date în ultimele 4 săptămâni
TZ = "Europe/Bucharest"


@dataclass
class WindowCheck:
    hh: np.ndarray
    issues: list[str] = field(default_factory=list)
    abstain_reason: str | None = None
    valid_days: int = 0


def check_window(hh: np.ndarray, recent: int = 28) -> WindowCheck:
    """Verifică fereastra unui contor (zile × 48, kWh pe 30 de minute)."""
    hh = np.array(hh, dtype=np.float64, copy=True)
    issues: list[str] = []
    bad = ~np.isfinite(hh) & ~np.isnan(hh)  # infinit
    if bad.any():
        hh[bad] = np.nan
        issues.append(f"{int(bad.sum())} valori infinite, tratate ca lipsă")
    day_valid = np.isfinite(hh).sum(axis=1) >= 40
    daily = np.where(day_valid, np.nansum(hh, axis=1), np.nan)
    pos = daily[np.isfinite(daily) & (daily > 0)]
    if pos.size and np.median(pos) > WH_SUSPECT_DAILY_KWH:
        hh = hh / 1000.0
        issues.append(f"valorile par în Wh (mediana {np.median(pos):.0f} pe zi), convertite în kWh")
    n_neg = int((hh < 0).sum())
    if n_neg:
        issues.append(f"{n_neg} citiri negative, păstrate ca semn de defect (polaritate inversată?)")
    n_big = int((hh > MAX_KWH_PER_HALFHOUR).sum())
    if n_big:
        issues.append(f"{n_big} citiri peste puterea unui branșament casnic, păstrate ca salturi false")
    valid_days = int(day_valid.sum())
    recent_days = int(day_valid[-recent:].sum())
    reason = None
    if valid_days < MIN_VALID_DAYS:
        reason = f"istoric prea scurt: doar {valid_days} zile cu date (minimum {MIN_VALID_DAYS})"
    elif recent_days < MIN_RECENT_DAYS:
        reason = f"prea puține date recente: {recent_days} zile cu date în ultimele 4 săptămâni"
    return WindowCheck(hh=hh, issues=issues, abstain_reason=reason, valid_days=valid_days)


def readings_to_halfhours(df: pd.DataFrame, start: str, end: str) -> tuple[np.ndarray, list[str]]:
    """Citiri brute -> tablou (zile × 48) în ora locală a României.

    `df` are coloanele `timestamp` și `kwh` (sfârșitul intervalului de 30 de minute). Tratează:
    - timestamp-uri fără fus orar: considerate ora României; cele ambigue la trecerea la ora de iarnă se mediază,
      cele inexistente la trecerea la ora de vară nu apar (intervalele rămân lipsă);
    - timestamp-uri dublate: se păstrează media și se notează;
    - valori nenumerice: lipsă; valori în Wh (mediana zilnică > 300): convertite în kWh.
    """
    issues: list[str] = []
    d = df.copy()
    d["kwh"] = pd.to_numeric(d["kwh"], errors="coerce")
    n_bad = int(d["kwh"].isna().sum())
    if n_bad:
        issues.append(f"{n_bad} valori nenumerice sau lipsă")
    ts = pd.to_datetime(d["timestamp"], errors="coerce", utc=False)
    n_bad_ts = int(ts.isna().sum())
    if n_bad_ts:
        issues.append(f"{n_bad_ts} timestamp-uri ilizibile, ignorate")
    d = d[ts.notna()].assign(timestamp=ts[ts.notna()])
    if d["timestamp"].dt.tz is None:
        local = d["timestamp"].dt.tz_localize(TZ, ambiguous="NaT", nonexistent="NaT")
        n_amb = int(local.isna().sum())
        if n_amb:
            issues.append(f"{n_amb} timestamp-uri ambigue sau inexistente la schimbarea orei, ignorate")
        d = d.assign(timestamp=local).dropna(subset=["timestamp"])
    else:
        d = d.assign(timestamp=d["timestamp"].dt.tz_convert(TZ))
    dup = d.duplicated(subset=["timestamp"], keep=False)
    if dup.any():
        issues.append(f"{int(dup.sum())} citiri cu timestamp dublat, mediate")
    d = d.groupby("timestamp", as_index=False)["kwh"].mean()
    begin = d["timestamp"] - pd.Timedelta(minutes=30)
    day0 = pd.Timestamp(start).date()
    n_days = (pd.Timestamp(end) - pd.Timestamp(start)).days + 1
    day_idx = np.array([(t.date() - day0).days for t in begin])
    slot = (begin.dt.hour * 2 + begin.dt.minute // 30).to_numpy()
    keep = (day_idx >= 0) & (day_idx < n_days)
    out = np.full((n_days, 48), np.nan)
    out[day_idx[keep], slot[keep]] = d["kwh"].to_numpy()[keep]
    check = check_window(out)
    return check.hh, issues + check.issues
