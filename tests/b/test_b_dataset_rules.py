"""Firul B: regula pentru valorile blocate din EAGLE-I (hartă înghețată), pe date construite în test."""

import pandas as pd

from cyberpunks.b_furtuna.dataset import _stuck_days


def _daily(values, pct_scale=1000.0):
    n = len(values)
    return pd.DataFrame({"fips": ["X"] * n, "date": pd.date_range("2024-01-01", periods=n, freq="D"),
                         "out_max": values, "pct_out_max": [v / pct_scale for v in values]})


def test_four_identical_days_are_flagged():
    d = _daily([10, 50, 50, 50, 50, 12])  # 4 zile la rând cu 50 (5% din 1.000 de clienți)
    flags = _stuck_days(d).tolist()
    assert flags == [False, True, True, True, True, False]


def test_three_identical_days_are_kept():
    d = _daily([10, 50, 50, 50, 12])
    assert not _stuck_days(d).any()


def test_small_repeated_values_are_kept():
    d = _daily([2, 2, 2, 2, 2, 2])  # 0,2% din clienți: zgomot obișnuit, nu hartă înghețată
    assert not _stuck_days(d).any()


def test_runs_do_not_cross_counties():
    a = _daily([50, 50])
    b = _daily([50, 50]).assign(fips="Y")
    assert not _stuck_days(pd.concat([a, b], ignore_index=True)).any()
