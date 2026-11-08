"""Firul B: regulile de decizie (abstain, intrări greșite, vreme lipsă) pe un model mic antrenat în test.

Datele de antrenare de aici sunt SINTETICE (generate în test), doar ca să verificăm logica, nu performanța.
"""

from datetime import date, datetime, time
from itertools import pairwise

import numpy as np
import pandas as pd
import pytest

from cyberpunks.b_furtuna import model as bmodel
from cyberpunks.b_furtuna import predict, romania
from cyberpunks.b_furtuna.features import FEATURES, make_features
from cyberpunks.common.contracts import WorkItem

TARGET = date(2025, 7, 8)
ECON = {"restoration_speedup_hours": 2.5, "cost_per_customer_hour_lei": 12}


@pytest.fixture(scope="module")
def tiny_model():
    """Model antrenat pe date SINTETICE: riscul crește cu rafala și cu ploaia."""
    rng = np.random.default_rng(0)
    n = 3000
    days = pd.date_range("2023-01-01", periods=730, freq="D")
    df = pd.DataFrame({
        "loc_id": rng.choice([f"S{i}" for i in range(8)], n),
        "date": rng.choice(days, n),
        "wind_gusts_10m_max": rng.gamma(4, 9, n),
        "wind_speed_10m_max": rng.gamma(4, 5, n),
        "precipitation_sum": rng.exponential(3, n),
        "rain_sum": rng.exponential(3, n),
        "snowfall_sum": np.zeros(n),
        "precipitation_hours": rng.integers(0, 12, n).astype(float),
        "temperature_2m_max": rng.normal(20, 8, n),
        "temperature_2m_min": rng.normal(10, 7, n),
        "shortwave_radiation_sum": rng.uniform(2, 30, n),
        "customers": rng.choice([15_000, 40_000, 120_000, 400_000], n),
        "area_km2": rng.uniform(800, 3000, n),
    })
    df = make_features(df).dropna(subset=["gust_prev", "precip_48h", "precip_7d", "snow_3d"])
    logit = -4 + 0.06 * (df["gust_max"] - 30) + 0.05 * df["precip_48h"]
    df["event"] = (rng.uniform(size=len(df)) < 1 / (1 + np.exp(-logit))).astype(int)
    df["pct_out_max"] = np.where(df["event"] == 1, rng.uniform(0.01, 0.2, len(df)), rng.uniform(0, 0.009, len(df)))
    df["y_log_pct"] = np.log1p(100 * df["pct_out_max"])
    df["wx_missing"] = False
    df["fips"], df["county"], df["state"] = df["loc_id"], "Synthetic", "SY"
    old = (bmodel.CLF_ROUNDS, bmodel.Q_ROUNDS)
    bmodel.CLF_ROUNDS, bmodel.Q_ROUNDS = 40, 40
    try:
        m, _ = bmodel.train(df, version="b-lgbm@test")
    finally:
        bmodel.CLF_ROUNDS, bmodel.Q_ROUNDS = old
    return m


def _feats(zones, gust=40.0, precip=5.0):
    rows = []
    for z in zones:
        rows.append({"zone_id": z.zone_id, "customers": z.customers, "area_km2": z.area_km2, "date": pd.Timestamp(TARGET),
                     "gust_max": gust, "wind_max": gust / 2, "gust_prev": 30.0, "gust_max_2d": max(gust, 30.0),
                     "precip": precip, "precip_48h": precip + 1, "precip_7d": precip + 5, "precip_hours": 3.0,
                     "snow": 0.0, "snow_3d": 0.0, "ice_proxy": 0.0, "tmax": 30.0, "tmin": 18.0, "t_range": 12.0,
                     "srad": 25.0})
    f = pd.DataFrame(rows)
    f["log_customers"] = np.log10(f["customers"])
    f["log_density"] = np.log10(f["customers"] / f["area_km2"])
    doy = f["date"].dt.dayofyear
    f["doy_sin"], f["doy_cos"] = np.sin(2 * np.pi * doy / 365.25), np.cos(2 * np.pi * doy / 365.25)
    f["precip_48h"] = f["precip_48h"].astype(float)
    return f


def _hourly(zones):
    hours = pd.date_range(f"{TARGET} 00:00", periods=24, freq="h")
    out = []
    for z in zones:
        g = np.where((hours.hour >= 15) & (hours.hour <= 18), 70.0, 25.0)
        out.append(pd.DataFrame({"time": hours, "wind_gusts_10m": g, "precipitation": np.where(hours.hour == 16, 8.0, 0.0),
                                 "zone_id": z.zone_id}))
    return pd.concat(out, ignore_index=True)


def _build(m, zones, feats, hourly=None, lo=None, hi=None):
    created = datetime.combine(date(2025, 7, 7), time(18, 0), tzinfo=predict.TZ)
    return predict.build_items(m, zones, feats, _hourly(zones) if hourly is None else hourly, TARGET, "historical",
                               created, ECON, "test", lo, hi, "test")


def test_items_are_valid_contracts_and_have_explanations(tiny_model):
    zones = [z for z in romania.load_zones() if z.region == "banat"]
    items, series = _build(tiny_model, zones, _feats(zones, gust=65.0, precip=15.0))
    assert len(items) == len(zones) == len(series)
    for it in items:
        WorkItem.model_validate(it.model_dump())
        assert it.work_item_id.startswith("B-20250708-")
        assert 1 <= len(it.explanation.top_factors) <= 8
        assert it.time_window.start.hour == 15  # furtuna începe la 15 (prima oră cu 70 km/h)
        assert abs(it.impact.expected_value_lei - it.prediction.score * it.impact.value_if_true_lei) <= 0.01
        assert it.prediction.interval_low <= it.prediction.score <= it.prediction.interval_high


def test_missing_weather_goes_to_human_review(tiny_model):
    zones = [z for z in romania.load_zones() if z.region == "banat"][:2]
    feats = _feats(zones)
    feats.loc[0, ["gust_max", "precip"]] = np.nan
    items, _ = _build(tiny_model, zones, feats)
    assert items[0].recommended_action == "human_review"
    assert items[0].prediction.abstain and "lipsesc" in items[0].prediction.abstain_reason
    assert any("vreme lipsă" in s for s in items[0].data_quality.input_issues)
    assert items[1].prediction.abstain is False or "lipsesc" not in (items[1].prediction.abstain_reason or "")


def test_out_of_range_zone_is_not_trusted_in_a_storm(tiny_model):
    zones = [z for z in romania.load_zones() if z.zone_id == "B-BUCURESTI"]  # 1 mil. clienți, peste antrenare
    items, _ = _build(tiny_model, zones, _feats(zones, gust=70.0, precip=25.0))
    assert items[0].recommended_action == "human_review"
    assert "antrenare" in items[0].prediction.abstain_reason


def test_out_of_range_zone_on_a_calm_day_is_not_sent_to_a_human(tiny_model):
    zones = [z for z in romania.load_zones() if z.zone_id == "B-BUCURESTI"]
    items, _ = _build(tiny_model, zones, _feats(zones, gust=20.0, precip=0.0))
    assert items[0].prediction.abstain is False
    assert any("vremea e liniștită" in s for s in items[0].data_quality.input_issues)


def test_extreme_gust_flags_safety_and_ood(tiny_model):
    zones = [z for z in romania.load_zones() if z.zone_id == "CS-RESITA"]
    items, _ = _build(tiny_model, zones, _feats(zones, gust=240.0))
    assert items[0].impact.safety_flag is True
    assert items[0].recommended_action == "human_review"


def test_weather_sources_disagree_means_human_review(tiny_model):
    zones = [z for z in romania.load_zones() if z.zone_id == "TM-LUGOJ"]
    feats = _feats(zones, gust=50.0)
    thr = tiny_model.decision_threshold
    items, _ = _build(tiny_model, zones, feats, lo=np.array([max(thr - 0.3, 0.0)]), hi=np.array([min(thr + 0.3, 1.0)]))
    assert items[0].recommended_action == "human_review"
    assert "nu se pun de acord" in items[0].prediction.abstain_reason


def test_no_hourly_weather_uses_afternoon_default(tiny_model):
    zones = [z for z in romania.load_zones() if z.zone_id == "AR-ARAD"]
    items, series = _build(tiny_model, zones, _feats(zones), hourly=pd.DataFrame())
    assert items[0].time_window.start.hour == 14  # implicit: după-amiaza, ora 14
    assert series[0].points[0].flag == "gol"


def test_target_features_keeps_zone_without_weather():
    zones = romania.load_zones()[:3]
    wx = pd.DataFrame()  # sursa meteo n-a răspuns deloc
    f = predict.target_features(zones, wx, TARGET)
    assert len(f) == 3
    assert f["gust_max"].isna().all()
    assert set(FEATURES) <= set(f.columns)


def test_run_without_weather_still_writes_valid_items(tmp_path, monkeypatch):
    """Open-Meteo picat și fără cache: B scrie totuși 26 de lucrări valide, toate la om, cu motivul spus."""
    from cyberpunks.b_furtuna import openmeteo

    def down(*a, **k):
        raise openmeteo.RateLimited("Daily API request limit exceeded")

    monkeypatch.setattr(openmeteo, "get", down)
    monkeypatch.setattr(predict, "OUTPUTS", tmp_path)
    monkeypatch.setattr(predict, "work_items_path", lambda s, src: tmp_path / "work_items" / s / f"{src}.jsonl")
    out = predict.run("demo-vara", None)
    lines = out.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 26
    items = [WorkItem.model_validate_json(x) for x in lines]
    assert all(it.recommended_action == "human_review" for it in items)
    assert all(any("vremea indisponibilă" in s for s in it.data_quality.input_issues) for it in items)


def test_series_carry_the_hourly_model_risk(tiny_model):
    """`expected` = riscul zilei estimat de model cu vremea de până la acea oră: 0-1, pe toate orele zilei, nu scade."""
    zones = [z for z in romania.load_zones() if z.zone_id == "TM-TIMISOARA"]
    _, series = _build(tiny_model, zones, _feats(zones, gust=70.0, precip=8.0))
    day = [pt for pt in series[0].points if pt.t.date() == TARGET]
    assert len(day) == 24
    risk = [pt.expected for pt in day]
    assert all(r is not None and 0.0 <= r <= 1.0 for r in risk)
    assert all(b >= a for a, b in pairwise(risk))  # curba nu scade
    assert risk[-1] > risk[0]  # furtuna de la 15:00 urcă riscul
