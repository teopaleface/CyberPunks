"""Firul B: curățarea vremii și features (fără rețea, date mici construite în test)."""

import numpy as np
import pandas as pd

from cyberpunks.b_furtuna.features import FEATURES, clean_weather, label_ro, make_features


def _wx(n=10, **over):
    d = pd.DataFrame({
        "loc_id": ["X"] * n,
        "date": pd.date_range("2025-07-01", periods=n, freq="D"),
        "weather_code": [3] * n,
        "temperature_2m_max": np.linspace(25, 35, n),
        "temperature_2m_min": np.linspace(15, 20, n),
        "precipitation_sum": [0, 0, 5, 10, 0, 0, 0, 2, 30, 1][:n],
        "rain_sum": [0, 0, 5, 10, 0, 0, 0, 2, 30, 1][:n],
        "snowfall_sum": [0.0] * n,
        "precipitation_hours": [0, 0, 2, 4, 0, 0, 0, 1, 6, 1][:n],
        "wind_speed_10m_max": [15.0] * n,
        "wind_gusts_10m_max": [30, 35, 40, 80, 30, 30, 30, 30, 95, 40][:n],
        "shortwave_radiation_sum": [25.0] * n,
        "customers": [50_000] * n,
        "area_km2": [2_000.0] * n,
    })
    for k, v in over.items():
        d[k] = v
    return d


def test_clean_weather_flags_impossible_values():
    wx = _wx()
    wx.loc[2, "wind_gusts_10m_max"] = 900.0  # imposibil
    wx.loc[3, "precipitation_sum"] = -4.0  # imposibil
    wx.loc[4, "temperature_2m_min"] = 40.0  # minima peste maxima
    clean, issues = clean_weather(wx)
    assert np.isnan(clean.loc[2, "wind_gusts_10m_max"])
    assert np.isnan(clean.loc[3, "precipitation_sum"])
    assert clean.loc[4, "temperature_2m_min"] <= clean.loc[4, "temperature_2m_max"]
    assert len(issues) == 3
    assert all(isinstance(s, str) and s for s in issues)


def test_make_features_lags_and_sums():
    f = make_features(_wx())
    assert set(FEATURES) <= set(f.columns)
    r = f.iloc[8]
    assert r["gust_max"] == 95
    assert r["gust_prev"] == 30
    assert r["precip_48h"] == 32  # 30 azi + 2 ieri
    assert r["precip_7d"] == 5 + 10 + 0 + 0 + 0 + 2 + 30  # zilele 2-8
    assert np.isnan(f.iloc[0]["gust_prev"])  # prima zi nu are ajun
    assert r["log_customers"] == np.log10(50_000)


def test_ice_proxy_only_when_freezing():
    wx = _wx(temperature_2m_min=[-2.0] * 10, temperature_2m_max=[1.0] * 10)
    f = make_features(wx)
    assert f.iloc[3]["ice_proxy"] == 10  # ploaie de 10 mm cu minima sub 0
    f2 = make_features(_wx())
    assert (f2["ice_proxy"] == 0).all()


def test_label_ro_is_plain_romanian():
    row = make_features(_wx()).iloc[8]
    text, val = label_ro("gust_max", row)
    assert text == "rafale de vânt de 95 km/h"
    assert val == 95
    text, _ = label_ro("log_customers", row)
    assert "50000" in text
