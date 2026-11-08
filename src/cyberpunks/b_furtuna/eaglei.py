"""Citirea EAGLE-I și agregarea pe comitat × oră (UTC) și pe comitat × zi (ora locală).

Fișierele anuale au coloanele fips_code, county, state, customers_out, run_start_time
(2023: `sum` în loc de `customers_out`; 2024+: în plus `total_customers`). Ora e UTC.
Un rând = un instantaneu la 15 minute; rândurile cu zero clienți afectați lipsesc.

    uv run python -m cyberpunks.b_furtuna.eaglei hourly --years 2023-2025
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as pacsv

from cyberpunks.b_furtuna.download import EAGLEI_DIR, parse_years
from cyberpunks.b_furtuna.manifest import eaglei_year_file
from cyberpunks.common.paths import DATA_INTERIM

# Statele din eșantion: acoperire EAGLE-I peste 90% din clienți în 2020-2022 și climă continentală,
# apropiată de a României (furtuni convective vara, gheață și zăpadă iarna).
STATES = {
    "Ohio": "OH",
    "Pennsylvania": "PA",
    "New York": "NY",
    "Virginia": "VA",
    "Michigan": "MI",
    "Illinois": "IL",
    "Missouri": "MO",
    "Kentucky": "KY",
}

HOURLY_DIR = DATA_INTERIM / "B" / "eaglei_hourly"


def read_year(year: int, states: dict[str, str] | None = None) -> pd.DataFrame:
    """Rândurile brute dintr-un an, doar pentru statele cerute: fips, ts_utc, customers_out."""
    states = states or STATES
    path = EAGLEI_DIR / eaglei_year_file(year)
    head = path.open(encoding="utf-8").readline().strip().split(",")
    out_col = "customers_out" if "customers_out" in head else "sum"
    convert = pacsv.ConvertOptions(
        include_columns=["fips_code", "state", out_col, "run_start_time"],
        column_types={"fips_code": pa.string(), "state": pa.string(), out_col: pa.float64(), "run_start_time": pa.string()},
    )
    table = pacsv.read_csv(path, read_options=pacsv.ReadOptions(block_size=1 << 26), convert_options=convert)
    mask = pc.is_in(table["state"], value_set=pa.array(list(states)))
    table = table.filter(mask)
    df = table.to_pandas()
    df = df.rename(columns={out_col: "customers_out", "fips_code": "fips"})
    df["fips"] = df["fips"].str.zfill(5)
    df["ts_utc"] = pd.to_datetime(df["run_start_time"], utc=True, format="mixed")
    df["customers_out"] = df["customers_out"].fillna(0).clip(lower=0)
    return df[["fips", "ts_utc", "customers_out"]]


def to_hourly(df: pd.DataFrame) -> pd.DataFrame:
    """Comitat × oră UTC: maximul instantaneelor, suma (pentru clienți-ore) și câte instantanee au fost."""
    df = df.assign(hour_utc=df["ts_utc"].dt.floor("h"))
    g = df.groupby(["fips", "hour_utc"], sort=False)["customers_out"]
    return g.agg(out_max="max", out_sum="sum", n_snap="size").reset_index()


def build_hourly(years: list[int]) -> list[Path]:
    HOURLY_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for y in years:
        dest = HOURLY_DIR / f"{y}.parquet"
        raw = read_year(y)
        hourly = to_hourly(raw)
        hourly.to_parquet(dest, index=False)
        print(f"{y}: {len(raw):,} instantanee -> {len(hourly):,} comitat-ore, {hourly['fips'].nunique()} comitate -> {dest}")
        written.append(dest)
    return written


def load_hourly(years: list[int]) -> pd.DataFrame:
    return pd.concat([pd.read_parquet(HOURLY_DIR / f"{y}.parquet") for y in years], ignore_index=True)


def to_daily_local(hourly: pd.DataFrame, tz_by_fips: dict[str, str]) -> pd.DataFrame:
    """Comitat × zi locală: vârful de clienți fără curent, clienți-ore, ore cu date.

    Clienții-ore se aproximează din instantaneele la 15 minute: suma × 0,25 h.
    """
    parts = []
    for tz, fips_list in pd.Series(tz_by_fips).groupby(lambda f: tz_by_fips[f]):
        sub = hourly[hourly["fips"].isin(fips_list.index)]
        if sub.empty:
            continue
        local_day = sub["hour_utc"].dt.tz_convert(tz).dt.date
        parts.append(sub.assign(date=local_day))
    daily_src = pd.concat(parts, ignore_index=True)
    g = daily_src.groupby(["fips", "date"])
    daily = g.agg(out_max=("out_max", "max"), out_sum=("out_sum", "sum"), hours_with_out=("out_max", "size")).reset_index()
    daily["customer_hours"] = daily.pop("out_sum") * 0.25
    daily["date"] = pd.to_datetime(daily["date"])
    return daily


def coverage(hourly: pd.DataFrame, year: int) -> pd.DataFrame:
    """Pe comitat: în câte zile (UTC) din an apare cel puțin un rând. Indicator de acoperire."""
    sub = hourly[hourly["hour_utc"].dt.year == year]
    days = sub.assign(d=sub["hour_utc"].dt.date).groupby("fips")["d"].nunique()
    n_days = 366 if year % 4 == 0 else 365
    return (days / n_days).rename(f"cov_{year}").reset_index()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["hourly"])
    ap.add_argument("--years", default="2023-2025")
    args = ap.parse_args(argv)
    if args.cmd == "hourly":
        build_hourly(parse_years(args.years))
    return 0


if __name__ == "__main__":
    np.seterr(all="ignore")
    raise SystemExit(main())
