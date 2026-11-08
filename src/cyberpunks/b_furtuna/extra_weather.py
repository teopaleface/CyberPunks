"""Variabile meteo NOI pentru B (experiment pe ramura Eden, nu intră în modelul livrat fără decizia echipei).

Două surse, aceleași la antrenare (comitate SUA) și la aplicare (zone România):
- arhiva ERA5 (`archive-api`), orar: rafale (ore peste prag), umiditatea solului 0-7 și 7-28 cm (copaci smulși),
  presiunea la nivelul mării (cicloni, scădere în 24 h), stratul de zăpadă, punctul de rouă, umiditatea, direcția
  vântului, înălțimea stratului limită, apa precipitabilă (aer umed, convecție);
- prognozele istorice GFS (`historical-forecast-api`, din 2023), orar: CAPE și indicele de stabilitate (lifted index),
  energia furtunilor de vară. Arhiva ERA5 din Open-Meteo nu are CAPE.

    uv run python -m cyberpunks.b_furtuna.extra_weather download   # ~7.600 de apeluri pentru 80 de comitate
    uv run python -m cyberpunks.b_furtuna.extra_weather build      # data/processed/B/us_extra_daily.parquet

Costul măsurat (7 nov. 2026): 78,8 apeluri pe comitat pentru ERA5 (10 variabile, 3 ani) și 15,7 pentru GFS.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import UTC, datetime

import numpy as np
import pandas as pd

from cyberpunks.b_furtuna import openmeteo
from cyberpunks.b_furtuna.us_sample import SAMPLE_CSV
from cyberpunks.common.paths import DATA_PROCESSED

ERA5_VARS = [
    "wind_gusts_10m",
    "soil_moisture_0_to_7cm",
    "soil_moisture_7_to_28cm",
    "pressure_msl",
    "snow_depth",
    "dew_point_2m",
    "relative_humidity_2m",
    "wind_direction_10m",
    "boundary_layer_height",
    "total_column_integrated_water_vapour",
]
GFS_VARS = ["cape", "lifted_index"]
# perioada -> (început ERA5, început GFS, sfârșit); „2021” = anii de antrenare în plus (vezi more_years.py)
PERIODS = {"2023": ("2022-12-25", "2023-01-01", "2025-12-31"), "2021": ("2020-12-25", "2021-01-01", "2022-12-31")}

EXTRA_DIR = openmeteo.OM_DIR / "us_extra"
OUT = DATA_PROCESSED / "B" / "us_extra_daily.parquet"


def _fetch(kind: str, lat: float, lon: float, period: str = "2023", attempts: int = 4) -> tuple[dict, float]:
    """Open-Meteo răspunde uneori cu HTTP 200 și textul „timeoutReached” în loc de JSON: reîncercăm."""
    for attempt in range(1, attempts + 1):
        try:
            return _fetch_once(kind, lat, lon, period)
        except ValueError as exc:  # JSONDecodeError
            if attempt == attempts:
                raise
            print(f"răspuns invalid de la Open-Meteo ({exc}), reîncerc în {30 * attempt} s", flush=True)
            time.sleep(30 * attempt)
    raise RuntimeError("nu ar trebui să ajungem aici")


def _fetch_once(kind: str, lat: float, lon: float, period: str) -> tuple[dict, float]:
    start, gfs_start, end = PERIODS[period]
    if kind == "era5":
        params = {"latitude": f"{lat:.4f}", "longitude": f"{lon:.4f}", "start_date": start, "end_date": end,
                  "hourly": ",".join(ERA5_VARS), "timezone": "auto"}
        data, cost = openmeteo.get(openmeteo.ARCHIVE, params, use_cache=False)
    else:
        params = {"latitude": f"{lat:.4f}", "longitude": f"{lon:.4f}", "start_date": gfs_start, "end_date": end,
                  "hourly": ",".join(GFS_VARS), "models": "gfs_seamless", "timezone": "auto"}
        data, cost = openmeteo.get(openmeteo.HIST_FORECAST, params, use_cache=False)
    return data, cost


def download(calls_per_hour: float = 3000.0, kinds: tuple[str, ...] = ("era5", "gfs"), period: str = "2023") -> None:
    counties = pd.read_csv(SAMPLE_CSV, dtype={"fips": str})
    EXTRA_DIR.mkdir(parents=True, exist_ok=True)
    spent = 0.0
    for kind in kinds:
        for i, c in counties.iterrows():
            dest = EXTRA_DIR / (f"{c['fips']}_{kind}.json" if period == "2023" else f"{c['fips']}_{kind}_p{period}.json")
            if dest.exists():
                continue
            t0 = time.time()
            data, cost = _fetch(kind, float(c["lat"]), float(c["lon"]), period)
            data["_meta"] = {"fips": c["fips"], "kind": kind, "fetched_utc": datetime.now(UTC).isoformat(timespec="seconds")}
            dest.write_text(json.dumps(data), encoding="utf-8")
            spent += cost
            print(f"{kind} {i + 1:3d}/{len(counties)} {c['fips']} {c['county']}: cost {cost:.1f}, total {spent:.0f}", flush=True)
            pause = cost / (calls_per_hour / 3600.0) - (time.time() - t0)
            if pause > 0:
                time.sleep(pause)
    print(f"gata, cost total {spent:.0f} apeluri")


def daily_from_hourly(h: pd.DataFrame) -> pd.DataFrame:
    """Agregatele zilnice (ora locală) ale variabilelor orare. Funcția servește și pentru prognoza din România."""
    h = h.copy()
    h["date"] = pd.to_datetime(h["time"]).dt.normalize()
    g = h.groupby("date")
    out = pd.DataFrame(index=g.size().index)
    if "wind_gusts_10m" in h:
        out["gust_hours_50"] = g["wind_gusts_10m"].apply(lambda s: float((s >= 50).sum()) if s.notna().any() else np.nan)
        out["gust_hours_70"] = g["wind_gusts_10m"].apply(lambda s: float((s >= 70).sum()) if s.notna().any() else np.nan)
        # direcția vântului la ora rafalei maxime (sin/cos)
        idx = h["wind_gusts_10m"].fillna(-1).groupby(h["date"]).idxmax()
        rad = np.deg2rad(h.loc[idx, "wind_direction_10m"].to_numpy(dtype=float)) if "wind_direction_10m" in h else None
        if rad is not None:
            out["gust_dir_sin"], out["gust_dir_cos"] = np.sin(rad), np.cos(rad)
    for col, name, how in [
        ("soil_moisture_0_to_7cm", "soil_top", "mean"),
        ("soil_moisture_7_to_28cm", "soil_root", "mean"),
        ("pressure_msl", "pmsl_min", "min"),
        ("pressure_msl", "pmsl_mean", "mean"),
        ("snow_depth", "snow_depth_max", "max"),
        ("dew_point_2m", "dew_max", "max"),
        ("relative_humidity_2m", "rh_mean", "mean"),
        ("boundary_layer_height", "blh_max", "max"),
        ("total_column_integrated_water_vapour", "tcwv_max", "max"),
        ("cape", "cape_max", "max"),
        ("lifted_index", "li_min", "min"),
    ]:
        if col in h:
            out[name] = getattr(g[col], how)()
    if "pressure_msl" in h:
        # cea mai mare scădere de presiune în 6 ore din ziua respectivă (semnul unui front sau al unui ciclon)
        drop6 = h["pressure_msl"].shift(6) - h["pressure_msl"]
        out["pmsl_drop6_max"] = drop6.groupby(h["date"]).max()
    return out.reset_index()


def _load_kind(kind: str) -> pd.DataFrame:
    frames = []
    for p in sorted(EXTRA_DIR.glob(f"*_{kind}*.json")):
        payload = json.loads(p.read_text(encoding="utf-8"))
        h = pd.DataFrame(payload["hourly"])
        d = daily_from_hourly(h)
        d["fips"] = payload["_meta"]["fips"]
        frames.append(d)
    if not frames:
        return pd.DataFrame(columns=["fips", "date"])
    return pd.concat(frames, ignore_index=True).drop_duplicates(["fips", "date"]).reset_index(drop=True)


def add_lags(df: pd.DataFrame, group: str = "fips") -> pd.DataFrame:
    """Variabilele care depind de ziua de ieri: scăderea presiunii în 24 h și solul din ziua precedentă."""
    df = df.sort_values([group, "date"]).copy()
    g = df.groupby(group, sort=False)
    if "pmsl_mean" in df:
        df["pmsl_drop24"] = g["pmsl_mean"].shift(1) - df["pmsl_min"]
    if "soil_root" in df:
        df["soil_root_prev"] = g["soil_root"].shift(1)
    if "cape_max" in df:
        df["cape_max_2d"] = np.fmax(df["cape_max"], g["cape_max"].shift(1))
    return df


def build() -> pd.DataFrame:
    era5, gfs = _load_kind("era5"), _load_kind("gfs")
    df = era5.merge(gfs, on=["fips", "date"], how="outer") if len(gfs) else era5
    df = add_lags(df)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False, compression="zstd")
    print(f"{len(df):,} zile-comitat, {df['fips'].nunique()} comitate, coloane: {[c for c in df if c not in ('fips', 'date')]}")
    return df


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["download", "build"])
    ap.add_argument("--calls-per-hour", type=float, default=3000.0)
    ap.add_argument("--kinds", default="era5,gfs")
    ap.add_argument("--period", default="2023", choices=sorted(PERIODS))
    a = ap.parse_args(argv)
    if a.cmd == "download":
        download(a.calls_per_hour, tuple(a.kinds.split(",")), a.period)
    else:
        build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
