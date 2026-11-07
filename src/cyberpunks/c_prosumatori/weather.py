"""Meteo pentru București-Ilfov din Open-Meteo (CC BY 4.0) și producția fotovoltaică pe kWp.

Toate orele sunt în UTC, „ora care se încheie”: valoarea de la ora H e media intervalului H-1..H (convenția
Open-Meteo pentru radiație). Descărcările stau în `data/raw/C/` (în afara git); sumele de control intră în
`data/samples/C/checksums.sha256`.

    uv run python -m cyberpunks.c_prosumatori.weather archive 2023-01-01 2026-11-06
    uv run python -m cyberpunks.c_prosumatori.weather forecast 2026-11-08 2026-11-09
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from cyberpunks.common.paths import DATA_RAW, DATA_SAMPLES

LAT, LON = 44.45, 26.05  # Ilfov / București (punctul de grilă Open-Meteo: 44,464 N 26,089 E)
TZ = "Europe/Bucharest"
VARS = "shortwave_radiation,direct_radiation,diffuse_radiation,global_tilted_irradiance,temperature_2m,cloud_cover"
RAW = DATA_RAW / "C"
UA = {"User-Agent": "CyberPunks-hackathon/0.1"}
COLS = {
    "shortwave_radiation": "ghi",
    "direct_radiation": "dir",
    "diffuse_radiation": "dif",
    "global_tilted_irradiance": "gti",
    "temperature_2m": "temp",
    "cloud_cover": "cloud",
}

# Modelul PV pe kWp (IPOTEZĂ calibrată pe PVGIS: 1.282 kWh/kWp pe an în Ilfov, cu pierderi de 14%)
PR = 0.86  # pierderi în afara temperaturii: invertor, cabluri, murdărie, nepotriviri
GAMMA = -0.0037  # pierdere de putere pe grad peste 25 °C (siliciu cristalin)
NOCT_K = 0.03125  # încălzirea celulei: (NOCT 45 - 20) / 800, °C per W/m²


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record_checksum(path: Path) -> str:
    """Scrie suma de control a unei descărcări în data/samples/C/checksums.sha256."""
    digest = _sha256(path)
    out = DATA_SAMPLES / "C" / "checksums.sha256"
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [ln for ln in (out.read_text().splitlines() if out.exists() else []) if not ln.endswith(f"  {path.name}")]
    lines.append(f"{digest}  {path.name}")
    out.write_text("\n".join(sorted(lines, key=lambda s: s.split("  ")[1])) + "\n")
    return digest


def _get(url: str, params: dict, dest: Path) -> Path:
    import httpx

    r = httpx.get(url, params=params, headers=UA, timeout=120)
    r.raise_for_status()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(r.content)
    record_checksum(dest)
    return dest


def _params(start: str, end: str) -> dict:
    return {
        "latitude": LAT,
        "longitude": LON,
        "hourly": VARS,
        "tilt": 30,
        "azimuth": 0,
        "timezone": "GMT",
        "start_date": start,
        "end_date": end,
    }


def download_archive(start: str, end: str) -> Path:
    dest = RAW / f"openmeteo_archive_utc_{start}_{end}.json"
    if dest.exists():
        return dest
    return _get("https://archive-api.open-meteo.com/v1/archive", _params(start, end), dest)


def download_forecast(start: str, end: str, refresh: bool = False) -> Path:
    dest = RAW / f"openmeteo_forecast_utc_{start}_{end}.json"
    if dest.exists() and not refresh:
        return dest
    return _get("https://api.open-meteo.com/v1/forecast", _params(start, end), dest)


def download_historical_forecast(start: str, end: str) -> Path:
    dest = RAW / f"openmeteo_histfc_utc_{start}_{end}.json"
    if dest.exists():
        return dest
    return _get("https://historical-forecast-api.open-meteo.com/v1/forecast", _params(start, end), dest)


def read_openmeteo(path: Path) -> pd.DataFrame:
    """Citește un JSON Open-Meteo (timezone=GMT) într-un tabel orar indexat în UTC."""
    js = json.loads(Path(path).read_text())
    h = js["hourly"]
    df = pd.DataFrame({COLS[k]: h[k] for k in COLS if k in h})
    df.index = pd.to_datetime(h["time"]).tz_localize("UTC")
    df.index.name = "time_utc"
    return df


def pv_per_kwp(gti: np.ndarray, temp: np.ndarray) -> np.ndarray:
    """Puterea AC pe kWp (kW/kWp) pentru un panou spre sud la 30°, din GTI (W/m²) și temperatura aerului (°C)."""
    gti = np.clip(np.nan_to_num(np.asarray(gti, dtype=float)), 0.0, 1400.0)
    tcell = np.asarray(temp, dtype=float) + NOCT_K * gti
    return np.clip(gti / 1000.0 * PR * (1.0 + GAMMA * (tcell - 25.0)), 0.0, None)


def archive(start: str = "2023-01-01", end: str = "2026-11-06") -> pd.DataFrame:
    return read_openmeteo(download_archive(start, end))


def annual_yield_check(df: pd.DataFrame) -> dict[int, float]:
    """kWh/kWp pe an din modelul nostru (de comparat cu PVGIS, 1.282 kWh/kWp)."""
    p = pv_per_kwp(df["gti"].to_numpy(), df["temp"].to_numpy())
    s = pd.Series(p, index=df.index)
    return {int(y): round(float(v), 1) for y, v in s.groupby(s.index.year).sum().items() if s[s.index.year == y].size > 8000}


if __name__ == "__main__":
    cmd, *rest = sys.argv[1:] or ["archive"]
    if cmd == "archive":
        p = download_archive(*(rest or ["2023-01-01", "2026-11-06"]))
        df = read_openmeteo(p)
        print(p, len(df), "ore;", "kWh/kWp pe an:", annual_yield_check(df))
    elif cmd == "forecast":
        p = download_forecast(*rest, refresh=True)
        print(p, read_openmeteo(p).tz_convert(TZ).between_time("09:00", "16:00"))
    elif cmd == "histfc":
        print(download_historical_forecast(*rest))
