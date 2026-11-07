"""Alege comitatele din SUA pentru care cerem vremea (cota Open-Meteo e mică).

Reguli, în ordine:
1. statele din `eaglei.STATES`;
2. comitate cu 10.000-600.000 de clienți (MCC, ORNL 2022): fără comitate minuscule, unde o singură linie
   căzută înseamnă zeci de procente, și fără metropole, care nu seamănă cu zonele noastre;
3. acoperire EAGLE-I bună: rânduri în cel puțin 80% din zilele fiecărui an verificat;
4. eșantion stratificat pe terțile de mărime (clienți) în fiecare stat, cu sămânță fixă.

    uv run python -m cyberpunks.b_furtuna.us_sample --per-state 10 --check-years 2023,2025
Scrie `data/samples/B/us_counties.csv` (în git).
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from cyberpunks.b_furtuna import eaglei
from cyberpunks.b_furtuna.download import EAGLEI_DIR
from cyberpunks.common.paths import DATA_RAW, DATA_SAMPLES

GAZETTEER = DATA_RAW / "B" / "census" / "2024_Gaz_counties_national.txt"
GAZETTEER_URL = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2024_Gazetteer/2024_Gaz_counties_national.zip"
SAMPLE_CSV = DATA_SAMPLES / "B" / "us_counties.csv"


def load_mcc() -> pd.DataFrame:
    mcc = pd.read_csv(EAGLEI_DIR / "MCC.csv", encoding="utf-8-sig")
    mcc["fips"] = mcc["County_FIPS"].astype(str).str.zfill(5)
    return mcc.rename(columns={"Customers": "customers"})[["fips", "customers"]]


def load_gazetteer() -> pd.DataFrame:
    gz = pd.read_csv(GAZETTEER, sep="\t", dtype={"GEOID": str})
    gz.columns = [c.strip() for c in gz.columns]
    gz = gz.rename(
        columns={"GEOID": "fips", "USPS": "state", "NAME": "county", "INTPTLAT": "lat", "INTPTLONG": "lon"}
    )
    gz["area_km2"] = gz["ALAND"] / 1e6
    return gz[["fips", "state", "county", "lat", "lon", "area_km2"]]


def candidates(check_years: list[int]) -> pd.DataFrame:
    df = load_gazetteer().merge(load_mcc(), on="fips")
    df = df[df["state"].isin(set(eaglei.STATES.values()))]
    for y in check_years:
        cov = eaglei.coverage(eaglei.to_hourly(eaglei.read_year(y)), y)
        df = df.merge(cov, on="fips", how="left")
        df[f"cov_{y}"] = df[f"cov_{y}"].fillna(0.0)
    return df


def sample(df: pd.DataFrame, per_state: int, check_years: list[int], seed: int = 42) -> pd.DataFrame:
    ok = df["customers"].between(10_000, 600_000)
    for y in check_years:
        ok &= df[f"cov_{y}"] >= 0.8
    pool = df[ok].copy()
    rng = np.random.default_rng(seed)
    picked = []
    for _state, grp in pool.groupby("state"):
        grp = grp.sort_values("customers").reset_index(drop=True)
        terciles = np.array_split(np.arange(len(grp)), 3)
        k = [per_state // 3 + (1 if i < per_state % 3 else 0) for i in range(3)]
        for idx, n in zip(terciles, k, strict=True):
            take = rng.choice(idx, size=min(n, len(idx)), replace=False)
            picked.append(grp.iloc[sorted(take)])
    out = pd.concat(picked, ignore_index=True)
    out["density_cust_km2"] = out["customers"] / out["area_km2"]
    return out.sort_values(["state", "fips"]).reset_index(drop=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--per-state", type=int, default=10)
    ap.add_argument("--check-years", default="2023,2025")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args(argv)
    years = [int(y) for y in args.check_years.split(",")]
    df = candidates(years)
    out = sample(df, args.per_state, years, args.seed)
    SAMPLE_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(SAMPLE_CSV, index=False, float_format="%.5f")
    print(out.groupby("state")["customers"].agg(["size", "min", "median", "max"]))
    print(f"{len(out)} comitate -> {SAMPLE_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
