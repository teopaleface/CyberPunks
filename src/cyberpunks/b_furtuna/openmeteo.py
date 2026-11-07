"""Clientul Open-Meteo al firului B: istoric (archive), prognoze trecute, prognoză, ensemble.

Cota gratuită e pe adresa IP și o împarte tot laptopul (toate firele): 600 de apeluri pe minut,
5.000 pe oră, 10.000 pe zi. O cerere costă cam (variabile / 10) × (zile / 14) × locații apeluri;
costul real vine în antetul `X-RateLimit-Cost` și îl scriem în `data/raw/B/openmeteo/ledger.csv`.

    uv run python -m cyberpunks.b_furtuna.openmeteo us-history --start 2022-12-25 --end 2025-12-31
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pandas as pd

from cyberpunks.common.paths import DATA_RAW

ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"
HIST_FORECAST = "https://historical-forecast-api.open-meteo.com/v1/forecast"
FORECAST = "https://api.open-meteo.com/v1/forecast"
ENSEMBLE = "https://ensemble-api.open-meteo.com/v1/ensemble"

OM_DIR = DATA_RAW / "B" / "openmeteo"
LEDGER = OM_DIR / "ledger.csv"

# Aceleași 10 variabile zilnice la antrenare (SUA) și la aplicare (România).
DAILY_VARS = [
    "weather_code",
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "rain_sum",
    "snowfall_sum",
    "precipitation_hours",
    "wind_speed_10m_max",
    "wind_gusts_10m_max",
    "shortwave_radiation_sum",
]
HOURLY_VARS = ["wind_gusts_10m", "wind_speed_10m", "precipitation", "temperature_2m", "weather_code"]

USER_AGENT = "cyberpunks-smarthack-2026 (research, non-commercial)"


class RateLimited(RuntimeError):
    pass


def _log_cost(url: str, n_locations: int, cost: str | None, status: int) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    new = not LEDGER.exists()
    with open(LEDGER, "a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["ts_utc", "endpoint", "n_locations", "cost", "status"])
        w.writerow([datetime.now(UTC).isoformat(timespec="seconds"), url.split("?")[0], n_locations, cost, status])


def _get_live(url: str, params: dict, n_locations: int, retries: int, wait: float, timeout: float) -> tuple[object, float]:
    """GET cu reîncercări. Întoarce (json, cost). La 429 așteaptă, apoi renunță cu RateLimited."""
    for attempt in range(1, retries + 1):
        try:
            r = httpx.get(url, params=params, timeout=timeout, headers={"User-Agent": USER_AGENT})
        except httpx.HTTPError as exc:
            if attempt == retries:
                raise
            print(f"eroare de rețea ({exc}), reîncerc în {wait:.0f} s")
            time.sleep(wait)
            continue
        cost = r.headers.get("X-RateLimit-Cost")
        _log_cost(url, n_locations, cost, r.status_code)
        if r.status_code == 200:
            return r.json(), float(cost or 0)
        if r.status_code == 429:
            if attempt == retries:
                raise RateLimited(r.text[:300])
            print(f"429 de la Open-Meteo ({r.text[:120]}), aștept {wait:.0f} s")
            time.sleep(wait)
            wait *= 2
            continue
        raise RuntimeError(f"Open-Meteo HTTP {r.status_code}: {r.text[:300]}")
    raise RuntimeError("nu ar trebui să ajungem aici")


# Cache pe disc: arhiva și prognozele trecute nu se mai schimbă (păstrate permanent); prognoza și ensemble-ul
# se reîmprospătează după 3 ore. Dacă Open-Meteo nu răspunde, folosim ultima copie salvată și o notăm în STALE_NOTES.
CACHE_DIR = OM_DIR / "cache"
TTL_S: dict[str, float | None] = {ARCHIVE: None, HIST_FORECAST: None, FORECAST: 3 * 3600, ENSEMBLE: 3 * 3600}
STALE_NOTES: list[str] = []


def _cache_path(url: str, params: dict) -> Path:
    blob = json.dumps({"url": url, "params": params}, sort_keys=True, default=str)
    return CACHE_DIR / f"{hashlib.sha1(blob.encode('utf-8')).hexdigest()}.json"


def get(url: str, params: dict, n_locations: int = 1, retries: int = 4, use_cache: bool = True,
        fast: bool = False) -> tuple[object, float]:
    """GET cu cache și reîncercări. `fast=True`: puține reîncercări și timeout scurt (pentru agentul live)."""
    path = _cache_path(url, params)
    ttl = TTL_S.get(url, 0.0)
    if use_cache and path.exists():
        age = time.time() - path.stat().st_mtime
        if ttl is None or age < ttl:
            return json.loads(path.read_text(encoding="utf-8")), 0.0
    try:
        data, cost = _get_live(url, params, n_locations, 2 if fast else retries, 5.0 if fast else 30.0,
                               20.0 if fast else 120.0)
    except (httpx.HTTPError, RateLimited, RuntimeError) as exc:
        if use_cache and path.exists():
            age_h = (time.time() - path.stat().st_mtime) / 3600
            STALE_NOTES.append(f"Open-Meteo n-a răspuns ({type(exc).__name__}): am folosit datele salvate acum {age_h:.1f} h")
            return json.loads(path.read_text(encoding="utf-8")), 0.0
        raise
    if use_cache:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding="utf-8")
    return data, cost


def _coords(lats: list[float], lons: list[float]) -> dict:
    return {"latitude": ",".join(f"{x:.4f}" for x in lats), "longitude": ",".join(f"{x:.4f}" for x in lons)}


def daily_frame(payload: dict) -> pd.DataFrame:
    """Răspunsul unei locații -> tabel zilnic cu coloana `date`."""
    d = pd.DataFrame(payload["daily"])
    d["date"] = pd.to_datetime(d.pop("time"))
    return d


def hourly_frame(payload: dict) -> pd.DataFrame:
    h = pd.DataFrame(payload["hourly"])
    h["time"] = pd.to_datetime(h["time"])
    return h


def archive_daily(lats: list[float], lons: list[float], start: str, end: str, timezone: str = "auto",
                  use_cache: bool = True) -> list[dict]:
    params = {**_coords(lats, lons), "start_date": start, "end_date": end, "daily": ",".join(DAILY_VARS),
              "timezone": timezone}
    data, _ = get(ARCHIVE, params, n_locations=len(lats), use_cache=use_cache)
    return data if isinstance(data, list) else [data]


def archive_hourly(lats: list[float], lons: list[float], start: str, end: str, timezone: str = "auto") -> list[dict]:
    params = {**_coords(lats, lons), "start_date": start, "end_date": end, "hourly": ",".join(HOURLY_VARS),
              "timezone": timezone}
    data, _ = get(ARCHIVE, params, n_locations=len(lats))
    return data if isinstance(data, list) else [data]


def forecast(lats: list[float], lons: list[float], past_days: int = 2, forecast_days: int = 3,
             timezone: str = "Europe/Bucharest") -> list[dict]:
    params = {**_coords(lats, lons), "daily": ",".join(DAILY_VARS), "hourly": ",".join(HOURLY_VARS),
              "past_days": past_days, "forecast_days": forecast_days, "timezone": timezone}
    data, _ = get(FORECAST, params, n_locations=len(lats), fast=True)
    return data if isinstance(data, list) else [data]


def historical_forecast(lats: list[float], lons: list[float], start: str, end: str,
                        timezone: str = "Europe/Bucharest") -> list[dict]:
    params = {**_coords(lats, lons), "start_date": start, "end_date": end, "daily": ",".join(DAILY_VARS),
              "hourly": ",".join(HOURLY_VARS), "timezone": timezone}
    data, _ = get(HIST_FORECAST, params, n_locations=len(lats))
    return data if isinstance(data, list) else [data]


def ensemble_gusts(lats: list[float], lons: list[float], forecast_days: int = 3, model: str = "icon_seamless",
                   timezone: str = "Europe/Bucharest") -> list[dict]:
    """Rafalele orare din ensemble (un model, toți membrii). Scump: ~ membri/10 apeluri pe locație."""
    params = {**_coords(lats, lons), "hourly": "wind_gusts_10m,precipitation", "models": model,
              "forecast_days": forecast_days, "timezone": timezone}
    data, _ = get(ENSEMBLE, params, n_locations=len(lats), fast=True)
    return data if isinstance(data, list) else [data]


# ---------------------------------------------------------------------------------------------
# Istoricul pentru comitatele din eșantionul SUA, în ritm lent și cu reluare
# ---------------------------------------------------------------------------------------------

US_DIR = OM_DIR / "us"


def us_history(sample_csv: Path, start: str, end: str, calls_per_hour: float = 3600.0, limit: int | None = None) -> None:
    from cyberpunks.b_furtuna.us_sample import SAMPLE_CSV

    counties = pd.read_csv(sample_csv or SAMPLE_CSV, dtype={"fips": str})
    # ordine amestecată pe state: dacă ne oprim la jumătate, avem totuși toate statele
    counties["rk"] = counties.groupby("state").cumcount()
    counties = counties.sort_values(["rk", "state"]).reset_index(drop=True)
    US_DIR.mkdir(parents=True, exist_ok=True)
    spent = 0.0
    done = 0
    for _, c in counties.iterrows():
        dest = US_DIR / f"{c['fips']}_{start}_{end}.json"
        if dest.exists():
            continue
        t0 = time.time()
        payload = archive_daily([c["lat"]], [c["lon"]], start, end, use_cache=False)[0]
        payload["_meta"] = {"fips": c["fips"], "state": c["state"], "county": c["county"], "source": ARCHIVE,
                            "fetched_utc": datetime.now(UTC).isoformat(timespec="seconds")}
        dest.write_text(json.dumps(payload), encoding="utf-8")
        cost = float(pd.read_csv(LEDGER).iloc[-1]["cost"] or 0)
        spent += cost
        done += 1
        print(f"{done:3d} {c['state']} {c['fips']} {c['county']}: cost {cost:.1f}, total {spent:.0f}", flush=True)
        if limit and done >= limit:
            break
        # ritm: cost / (calls_per_hour / 3600) secunde pe cerere
        pause = cost / (calls_per_hour / 3600.0) - (time.time() - t0)
        if pause > 0:
            time.sleep(pause)
    print(f"gata: {done} comitate noi, cost total {spent:.0f} apeluri")


def load_us_history(start: str, end: str) -> pd.DataFrame:
    frames = []
    for p in sorted(US_DIR.glob(f"*_{start}_{end}.json")):
        payload = json.loads(p.read_text(encoding="utf-8"))
        d = daily_frame(payload)
        d["fips"] = payload["_meta"]["fips"]
        d["tz"] = payload.get("timezone")
        d["grid_lat"], d["grid_lon"] = payload.get("latitude"), payload.get("longitude")
        frames.append(d)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["us-history"])
    ap.add_argument("--sample", type=Path, default=None)
    ap.add_argument("--start", default="2022-12-25")
    ap.add_argument("--end", default="2025-12-31")
    ap.add_argument("--calls-per-hour", type=float, default=3600.0)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args(argv)
    if args.cmd == "us-history":
        us_history(args.sample, args.start, args.end, args.calls_per_hour, args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
