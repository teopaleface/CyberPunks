"""Zonele din România (aria Rețele Electrice) și vremea lor, pentru aplicarea modelului B.

Clienții pe județ sunt oficiali (Planul de dezvoltare RER 2026-2035, 31.12.2024). Împărțirea pe zone e a noastră:
ponderea unei zone = (populația orașului principal + restul populației județului împărțit egal) / populația
județului. E o APROXIMARE și apare ca atare în `data_quality.input_issues`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import pandas as pd
import yaml

from cyberpunks.b_furtuna import openmeteo
from cyberpunks.b_furtuna.features import clean_weather, make_features
from cyberpunks.common.paths import DATA_SAMPLES

ZONES_YAML = DATA_SAMPLES / "B" / "zones_ro.yaml"
LAG_DAYS = 8  # câte zile înainte cerem, pentru ploaia pe 7 zile și rafala din ajun


@dataclass(frozen=True)
class Zone:
    zone_id: str
    county_code: str
    county: str
    region: str
    label_ro: str
    lat: float
    lon: float
    customers: int
    area_km2: float
    customers_per_capita_county: float


def load_zones() -> list[Zone]:
    cfg = yaml.safe_load(ZONES_YAML.read_text(encoding="utf-8"))
    counties = cfg["counties"]
    by_county: dict[str, list[dict]] = {}
    for z in cfg["zones"]:
        by_county.setdefault(z["county_code"], []).append(z)
    zones = []
    for code, zs in by_county.items():
        c = counties[code]
        k = len(zs)
        towns = sum(min(z["town_population_2021"], c["population_2021"]) for z in zs)
        rest = max(c["population_2021"] - towns, 0)
        for z in zs:
            w = (min(z["town_population_2021"], c["population_2021"]) + rest / k) / c["population_2021"]
            zones.append(
                Zone(
                    zone_id=z["zone_id"],
                    county_code=code,
                    county=c["name"],
                    region=c["region"],
                    label_ro=z["label_ro"],
                    lat=float(z["lat"]),
                    lon=float(z["lon"]),
                    customers=round(c["customers"] * w),
                    area_km2=float(c["area_km2"]) / k,
                    customers_per_capita_county=c["customers"] / c["population_2021"],
                )
            )
    return zones


def zones_frame(zones: list[Zone] | None = None) -> pd.DataFrame:
    return pd.DataFrame([z.__dict__ for z in (zones or load_zones())])


def weather_daily(zones: list[Zone], target: date, mode: str) -> tuple[pd.DataFrame, list[str]]:
    """Vremea zilnică pentru zone, de la target-LAG_DAYS la target (sau până la target+1 pentru prognoză).

    mode: "historical" (arhiva Open-Meteo, aceeași sursă ca la antrenare) sau "forecast" (prognoza).
    """
    lats, lons = [z.lat for z in zones], [z.lon for z in zones]
    start = target - timedelta(days=LAG_DAYS)
    if mode == "historical":
        payloads = openmeteo.archive_daily(lats, lons, start.isoformat(), target.isoformat(), timezone="Europe/Bucharest")
    else:
        past = max((date.today() - start).days, 0)
        ahead = max((target - date.today()).days + 1, 1)
        payloads = openmeteo.forecast(lats, lons, past_days=min(past, 92), forecast_days=min(ahead + 1, 16))
    frames = []
    for z, p in zip(zones, payloads, strict=True):
        d = openmeteo.daily_frame(p)
        d = d[(d["date"] >= pd.Timestamp(start)) & (d["date"] <= pd.Timestamp(target))]
        d["zone_id"] = z.zone_id
        frames.append(d)
    wx = pd.concat(frames, ignore_index=True)
    wx, issues = clean_weather(wx)
    return wx, issues


def weather_daily_range(zones: list[Zone], start: date, end: date) -> tuple[pd.DataFrame, list[str]]:
    """Arhiva zilnică pentru un interval întreg (backtest), într-o singură cerere."""
    payloads = openmeteo.archive_daily([z.lat for z in zones], [z.lon for z in zones], start.isoformat(),
                                       end.isoformat(), timezone="Europe/Bucharest")
    frames = []
    for z, p in zip(zones, payloads, strict=True):
        d = openmeteo.daily_frame(p)
        d["zone_id"] = z.zone_id
        frames.append(d)
    return clean_weather(pd.concat(frames, ignore_index=True))


def weather_hourly_range(zones: list[Zone], start: date, end: date) -> pd.DataFrame:
    payloads = openmeteo.archive_hourly([z.lat for z in zones], [z.lon for z in zones], start.isoformat(),
                                        end.isoformat(), timezone="Europe/Bucharest")
    frames = []
    for z, p in zip(zones, payloads, strict=True):
        h = openmeteo.hourly_frame(p)
        h["zone_id"] = z.zone_id
        frames.append(h)
    return pd.concat(frames, ignore_index=True)


def weather_hourly(zones: list[Zone], target: date, mode: str) -> pd.DataFrame:
    lats, lons = [z.lat for z in zones], [z.lon for z in zones]
    if mode == "historical":
        payloads = openmeteo.archive_hourly(lats, lons, (target - timedelta(days=1)).isoformat(),
                                            (target + timedelta(days=1)).isoformat(), timezone="Europe/Bucharest")
    else:
        payloads = openmeteo.forecast(lats, lons, past_days=1, forecast_days=max((target - date.today()).days + 2, 2))
    frames = []
    for z, p in zip(zones, payloads, strict=True):
        h = openmeteo.hourly_frame(p)
        h["zone_id"] = z.zone_id
        frames.append(h)
    return pd.concat(frames, ignore_index=True)


def feature_table(zones: list[Zone], wx: pd.DataFrame, target: date) -> pd.DataFrame:
    """Features pentru ziua țintă, câte un rând pe zonă."""
    zf = zones_frame(zones)[["zone_id", "customers", "area_km2"]]
    df = wx.merge(zf, on="zone_id")
    df = make_features(df, group="zone_id")
    return df[df["date"] == pd.Timestamp(target)].reset_index(drop=True)
