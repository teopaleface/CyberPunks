"""Firul B: varianta europeană (SSEN). Tabelul district × zi din git e consecvent cu eticheta (fără rețea)."""

import pandas as pd

from cyberpunks.b_furtuna.ssen import DISTRICTS, SSEN_TABLE, WEATHER_CAUSES


def test_ssen_table_matches_the_label_rule():
    df = pd.read_parquet(SSEN_TABLE)
    assert set(df["district"].unique()) == set(DISTRICTS)
    assert (df["event"] == (df["n_weather"] >= 1).astype(int)).all()
    assert (df["severe"] == (df["n_weather"] >= 2).astype(int)).all()
    assert df["date"].min() == pd.Timestamp("2016-01-01")
    assert df["date"].max() == pd.Timestamp("2025-12-31")
    assert 0.05 < df["event"].mean() < 0.15  # circa 9% din zilele-district au avarii de vreme


def test_growing_trees_is_not_a_storm_cause():
    assert "Growing Trees" not in WEATHER_CAUSES  # creșterea vegetației nu e eveniment meteo
    assert "Wind and Gale (excluding Windborne Material)" in WEATHER_CAUSES
