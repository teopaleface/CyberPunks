"""Mai mulți ani de antrenare pentru B (experiment pe ramura Eden): 2021 și 2022, pentru aceleași 80 de comitate.

Tabelul livrat (`data/samples/B/us_county_day.parquet`) are 2023-2025. Aici construim aceleași rânduri pentru
2021-2022, cu exact aceeași curățare și aceleași features (`dataset.build`), apoi le lipim la tabelul livrat.
Anul de test rămâne 2025.

    uv run python -m cyberpunks.b_furtuna.download eaglei --years 2021-2022
    uv run python -m cyberpunks.b_furtuna.eaglei hourly --years 2021-2022
    uv run python -m cyberpunks.b_furtuna.more_years weather       # ~4.400 apeluri Open-Meteo (vremea zilnică)
    uv run python -m cyberpunks.b_furtuna.extra_weather download --period 2021   # variabilele noi, ~5.400 apeluri
    uv run python -m cyberpunks.b_furtuna.more_years build         # data/processed/B/us_county_day_2021_2022.parquet
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import UTC, datetime

import pandas as pd

from cyberpunks.b_furtuna import dataset, openmeteo
from cyberpunks.b_furtuna.us_sample import SAMPLE_CSV
from cyberpunks.common.paths import DATA_PROCESSED

START, END = "2020-12-25", "2022-12-31"  # 7 zile înainte de 2021, pentru întârzieri (ploaia pe 7 zile etc.)
WX_DIR = openmeteo.OM_DIR / "us_2021_2022"
OUT = DATA_PROCESSED / "B" / "us_county_day_2021_2022.parquet"
SUMMARY = DATA_PROCESSED / "B" / "us_county_day_2021_2022_summary.json"


def weather(calls_per_hour: float = 3600.0) -> None:
    counties = pd.read_csv(SAMPLE_CSV, dtype={"fips": str})
    WX_DIR.mkdir(parents=True, exist_ok=True)
    spent = 0.0
    for i, c in counties.iterrows():
        dest = WX_DIR / f"{c['fips']}.json"
        if dest.exists():
            continue
        t0 = time.time()
        for attempt in range(4):
            try:
                payload = openmeteo.archive_daily([c["lat"]], [c["lon"]], START, END, use_cache=False)[0]
                break
            except ValueError:  # Open-Meteo: HTTP 200 cu „timeoutReached” în loc de JSON
                time.sleep(30 * (attempt + 1))
        else:
            raise RuntimeError(f"Open-Meteo nu răspunde pentru {c['fips']}")
        payload["_meta"] = {"fips": c["fips"], "fetched_utc": datetime.now(UTC).isoformat(timespec="seconds")}
        dest.write_text(json.dumps(payload), encoding="utf-8")
        cost = float(pd.read_csv(openmeteo.LEDGER).iloc[-1]["cost"] or 0)
        spent += cost
        print(f"{i + 1:3d}/{len(counties)} {c['fips']} {c['county']}: cost {cost:.1f}, total {spent:.0f}", flush=True)
        pause = cost / (calls_per_hour / 3600.0) - (time.time() - t0)
        if pause > 0:
            time.sleep(pause)


def _load_weather() -> pd.DataFrame:
    frames = []
    for p in sorted(WX_DIR.glob("*.json")):
        payload = json.loads(p.read_text(encoding="utf-8"))
        d = openmeteo.daily_frame(payload)
        d["fips"] = payload["_meta"]["fips"]
        d["tz"] = payload.get("timezone")
        d["grid_lat"], d["grid_lon"] = payload.get("latitude"), payload.get("longitude")
        frames.append(d)
    return pd.concat(frames, ignore_index=True)


def build() -> pd.DataFrame:
    orig = openmeteo.load_us_history
    openmeteo.load_us_history = _load_weather
    try:
        df, summary = dataset.build()
    finally:
        openmeteo.load_us_history = orig
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False, compression="zstd")
    SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary["by_year"], indent=2))
    return df


def load_all() -> pd.DataFrame:
    """Tabelul livrat (2023-2025) plus 2021-2022, dacă au fost construite."""
    df = pd.read_parquet(dataset.OUT)
    if OUT.exists():
        extra = pd.read_parquet(OUT)
        df = pd.concat([extra[extra["year"].isin([2021, 2022])], df], ignore_index=True)
    df["date"] = pd.to_datetime(df["date"])
    return df


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["weather", "build"])
    a = ap.parse_args(argv)
    weather() if a.cmd == "weather" else build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
