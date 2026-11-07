"""Tabelul de antrenare: comitat × zi locală, EAGLE-I + vremea Open-Meteo + features.

    uv run python -m cyberpunks.b_furtuna.dataset
Scrie `data/processed/B/us_county_day.parquet` și afișează un rezumat.

Curățare (fiecare regulă e numărată în rezumat):
- comitat-an cu rânduri EAGLE-I în mai puțin de 50% din zile: scos (lipsa rândurilor ar fi citită greșit ca zero);
- vârf peste numărul de clienți (MCC e modelat): tăiat la 100%, numărat;
- valori „blocate” (același vârf ≥ 0,5% din clienți 4 zile la rând, semn de hartă înghețată): zilele scoase;
- vreme lipsă sau imposibilă: rândul scos din antrenare.
"""

from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd

from cyberpunks.b_furtuna import eaglei, openmeteo
from cyberpunks.b_furtuna.features import FEATURES, clean_weather, make_features
from cyberpunks.b_furtuna.us_sample import SAMPLE_CSV
from cyberpunks.common.paths import DATA_PROCESSED

EVENT_THRESHOLD = 0.01  # vârful zilei ≥ 1% din clienții zonei
STUCK_MIN_DAYS = 4  # același vârf (≥ 0,5% din clienți) atâtea zile la rând = hartă înghețată
SEVERE_THRESHOLD = 0.05
EXTREME_THRESHOLD = 0.10
LAG_DAYS = 7  # primele zile din fiecare interval de vreme servesc doar pentru întârzieri (ploaia pe 7 zile etc.)
OUT = DATA_PROCESSED / "B" / "us_county_day.parquet"
SUMMARY = DATA_PROCESSED / "B" / "us_county_day_summary.json"


def _stuck_days(daily: pd.DataFrame) -> pd.Series:
    """True pentru zilele dintr-un șir de ≥4 zile consecutive cu exact același vârf (≥0,5% din clienți)."""
    daily = daily.sort_values(["fips", "date"])
    same = (daily["out_max"] == daily.groupby("fips")["out_max"].shift(1)) & (daily["pct_out_max"] >= 0.005)
    run_id = (~same).cumsum()
    run_len = same.groupby(run_id).transform("size")
    # run_len = numărul de zile din șir (prima zi plus cele identice cu ziua de dinainte); cerem cel puțin 4
    flag = same & (run_len >= STUCK_MIN_DAYS)
    first = flag.groupby(run_id).transform("any") & ~same
    return (flag | first).reindex(daily.index)


def build(min_cov: float = 0.5) -> tuple[pd.DataFrame, dict]:
    sample = pd.read_csv(SAMPLE_CSV, dtype={"fips": str})
    wx = openmeteo.load_us_history()
    if wx.empty:
        raise SystemExit("Lipsește vremea: rulează întâi `python -m cyberpunks.b_furtuna.openmeteo us-history`.")
    wx, wx_issues = clean_weather(wx)
    have = sorted(set(wx["fips"]) & set(sample["fips"]))
    sample = sample[sample["fips"].isin(have)]
    tz_by_fips = wx.groupby("fips")["tz"].first().to_dict()

    years = sorted(y for y in wx["date"].dt.year.unique() if (eaglei.HOURLY_DIR / f"{y}.parquet").exists())
    hourly = eaglei.load_hourly(years)
    hourly = hourly[hourly["fips"].isin(have)]
    daily_out = eaglei.to_daily_local(hourly, tz_by_fips)

    df = wx.merge(daily_out, on=["fips", "date"], how="left")
    for c in ["out_max", "customer_hours", "hours_with_out"]:
        df[c] = df[c].fillna(0.0)
    df = df.merge(sample[["fips", "state", "county", "customers", "area_km2", "lat", "lon"]], on="fips")
    df["loc_id"] = df["fips"]
    df = make_features(df)
    first = df.groupby("fips")["date"].transform("min")
    df = df[(df["date"] >= first + pd.Timedelta(days=LAG_DAYS)) & df["date"].dt.year.isin(years)].copy()
    df["year"] = df["date"].dt.year

    summary: dict = {"counties": int(df["fips"].nunique()), "rows_raw": len(df), "weather_issues": wx_issues}

    # acoperire pe comitat-an: zile cu cel puțin un rând EAGLE-I
    cov = (df.assign(has=df["hours_with_out"] > 0).groupby(["fips", "year"])["has"].mean().rename("cov"))
    df = df.merge(cov.reset_index(), on=["fips", "year"])
    low = df["cov"] < min_cov
    summary["dropped_low_coverage_county_years"] = int(df.loc[low, ["fips", "year"]].drop_duplicates().shape[0])
    df = df[~low].copy()

    df["pct_out_max"] = df["out_max"] / df["customers"]
    over = df["pct_out_max"] > 1.0
    summary["clipped_over_100pct"] = int(over.sum())
    df["pct_out_max"] = df["pct_out_max"].clip(upper=1.0)

    stuck = _stuck_days(df)
    summary["dropped_stuck_days"] = int(stuck.sum())
    df = df[~stuck].copy()

    miss = df[FEATURES].isna().any(axis=1)
    summary["rows_missing_weather"] = int(miss.sum())
    df["wx_missing"] = miss

    df["event"] = (df["pct_out_max"] >= EVENT_THRESHOLD).astype(int)
    df["severe"] = (df["pct_out_max"] >= SEVERE_THRESHOLD).astype(int)
    df["extreme"] = (df["pct_out_max"] >= EXTREME_THRESHOLD).astype(int)
    df["y_log_pct"] = np.log1p(100.0 * df["pct_out_max"])  # ținta cuantilelor: log(1 + procent)

    summary["rows"] = len(df)
    by_year = df.groupby("year").agg(rows=("event", "size"), events=("event", "sum"), severe=("severe", "sum"),
                                     extreme=("extreme", "sum"))
    by_year["prevalence"] = (by_year["events"] / by_year["rows"]).round(4)
    summary["by_year"] = {int(k): {kk: float(vv) for kk, vv in v.items()} for k, v in by_year.to_dict("index").items()}
    summary["states"] = sorted(df["state"].unique().tolist())
    return df, summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--min-cov", type=float, default=0.5)
    args = ap.parse_args(argv)
    df, summary = build(args.min_cov)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)
    SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"-> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
