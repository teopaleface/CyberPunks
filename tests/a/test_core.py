"""Teste mici pentru metrici, calibrare, conformal, features și validarea intrărilor."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from cyberpunks.a_contoare import metrics as M
from cyberpunks.a_contoare.calibration import MondrianConformal, VennAbers
from cyberpunks.a_contoare.features import DAILY_FEATURES, INTRADAY_FEATURES, daily_features, intraday_features
from cyberpunks.a_contoare.validate import check_window, readings_to_halfhours


def test_precision_at_k_breaks_ties_randomly() -> None:
    y = np.array([1] * 10 + [0] * 90)  # primele rânduri sunt pozitive, ca în SGCC
    flat = np.zeros(100)
    assert M.precision_at_k(y, flat, 10) < 0.6  # o sortare stabilă ar da 1.0


def test_venn_abers_interval_contains_score() -> None:
    rng = np.random.default_rng(0)
    s = rng.random(2000)
    y = (rng.random(2000) < s**2).astype(int)
    p, p0, p1 = VennAbers(grid_size=100).fit(s, y).predict(rng.random(500))
    assert np.all(p0 <= p + 1e-12) and np.all(p <= p1 + 1e-12)


def test_conformal_coverage_on_exchangeable_data() -> None:
    rng = np.random.default_rng(1)
    p = rng.random(20000)
    y = (rng.random(20000) < p).astype(int)
    c = MondrianConformal(alpha_normal=0.1, alpha_problem=0.1).fit(p[:10000], y[:10000])
    cov = c.coverage(p[10000:], y[10000:])
    assert cov["set_coverage_normal"] >= 0.88 and cov["set_coverage_problem"] >= 0.88


def test_conformal_quantile_is_kth_order_statistic() -> None:
    scores = np.arange(1, 11) / 10.0  # 0,1 ... 1,0
    assert MondrianConformal._quantile(scores, 0.3) == 0.8  # k = ceil(11 × 0,7) = 8 -> a 8-a valoare
    assert MondrianConformal._quantile(np.array([0.4]), 0.05) == 1.0  # k > n: clasa se include mereu


def test_ece_with_constant_probabilities() -> None:
    y = np.array([0, 0, 0, 1])
    p = np.full(4, 0.5)
    assert abs(M.ece(y, p) - 0.25) < 1e-12
    assert len(M.reliability_table(y, p)) == 1


def test_paired_bootstrap_accepts_groups() -> None:
    rng = np.random.default_rng(3)
    y = (rng.random(400) < 0.2).astype(int)
    good, bad = y + rng.normal(0, 0.3, 400), rng.random(400)
    groups = np.repeat(np.arange(100), 4)
    win = M.paired_bootstrap_win(M.pr_auc, y, good, bad, n=50, groups=groups)
    assert win > 0.9


def test_daily_features_detect_zero_run_and_drop() -> None:
    x = np.full((2, 180), 10.0)
    x[0, -15:] = 0.0  # contor oprit de 15 zile
    x[1, -28:] = 4.0  # scădere de 60%
    f = daily_features(x, np.full(180, 10.0))
    assert list(f.columns) == DAILY_FEATURES
    assert f.loc[0, "zero_run_recent"] == 15
    assert abs(f.loc[1, "recent_vs_base"] - 0.4) < 1e-3


def test_intraday_features_shape_and_flat_profile() -> None:
    rng = np.random.default_rng(2)
    prof = 0.2 + 0.3 * np.sin(np.linspace(0, 2 * np.pi, 48)) ** 2
    base = np.tile(prof, (1, 56, 1)) * rng.uniform(0.9, 1.1, (1, 56, 48))
    flat = np.tile(prof.mean(), (1, 28, 48))  # atacul h4: media zilei în fiecare interval
    f = intraday_features(flat, base)
    assert list(f.columns) == INTRADAY_FEATURES
    assert f.loc[0, "intraday_cv_recent"] < 0.01


def test_check_window_converts_wh_and_flags_short_history() -> None:
    hh = np.full((180, 48), 0.3) * 1000  # 14,4 kWh/zi trimiși în Wh
    out = check_window(hh)
    assert abs(np.nanmedian(out.hh) - 0.3) < 1e-9 and any("Wh" in i for i in out.issues)
    assert out.abstain_reason and "unitate" in out.abstain_reason  # ambiguu: decide un om, nu reparăm în tăcere
    short = np.full((180, 48), np.nan)
    short[-20:] = 0.3
    assert check_window(short).abstain_reason.startswith("istoric prea scurt")


def test_readings_handle_duplicates_and_dst() -> None:
    ts = pd.date_range("2026-03-28 00:30", "2026-03-30 00:00", freq="30min")  # trecerea la ora de vară: 29 martie
    df = pd.DataFrame({"timestamp": ts.astype(str), "kwh": 0.25})
    df = pd.concat([df, df.iloc[[5]]], ignore_index=True)  # un timestamp dublat
    df.loc[3, "kwh"] = "eroare"
    hh, issues = readings_to_halfhours(df, "2026-03-28", "2026-03-29")
    assert hh.shape == (2, 48)
    assert any("dublat" in i for i in issues) and any("nenumerice" in i for i in issues)
    assert any("schimbarea orei" in i for i in issues)


def test_autumn_dst_repeated_hour_is_summed_for_aware_timestamps() -> None:
    # 25 oct. 2026: ora 04:00 (EEST) devine 03:00 (EET), deci 03:00-04:00 ora locală apare de două ori
    ts = pd.date_range("2026-10-24 21:30", "2026-10-25 22:00", freq="30min", tz="UTC")
    df = pd.DataFrame({"timestamp": ts, "kwh": 0.2})
    hh, issues = readings_to_halfhours(df, "2026-10-25", "2026-10-25")
    assert any("ora de iarnă" in i for i in issues)
    assert hh[0, 6] == pytest.approx(0.4)  # 03:00-03:30 ora locală, de două ori
    assert np.nansum(hh[0]) == pytest.approx(0.2 * 50)  # ziua are 25 de ore = 50 de intervale
