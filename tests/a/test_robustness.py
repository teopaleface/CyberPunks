"""Robustețe: intrări greșite, date lipsă, istoric scurt, surse lipsă și determinism (firul A)."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest

from cyberpunks.a_contoare import demo
from cyberpunks.a_contoare.features import daily_features, intraday_features
from cyberpunks.a_contoare.lcl import INTRADAY_BASE, RECENT, daily_from_halfhours, quantize
from cyberpunks.a_contoare.model import MeterModel
from cyberpunks.a_contoare.validate import MAX_KWH_PER_HALFHOUR, check_window, readings_to_halfhours


def _household(seed: int = 0, days: int = 180) -> np.ndarray:
    """O gospodărie plauzibilă: profil de zi cu dimineață și seară, variație pe zi, rezoluție de contor."""
    rng = np.random.default_rng(seed)
    t = np.arange(48)
    prof = 0.08 + 0.25 * np.exp(-((t - 15) ** 2) / 8) + 0.45 * np.exp(-((t - 39) ** 2) / 12)
    hh = prof[None, :] * rng.uniform(0.8, 1.2, (days, 1)) * rng.uniform(0.85, 1.15, (days, 48))
    return quantize(hh)


def _score(windows: list[np.ndarray]) -> pd.DataFrame:
    model = MeterModel.load("a-lgbm")
    checks = [check_window(w) for w in windows]
    hh = np.stack([c.hh for c in checks])
    daily = daily_from_halfhours(hh)
    peers = np.stack([daily_from_halfhours(_household(s)) for s in range(10, 30)])
    with np.errstate(all="ignore"):
        peer = np.nanmedian(peers, axis=0)
    feats = pd.concat(
        [daily_features(daily, peer), intraday_features(hh[:, -RECENT:], hh[:, -RECENT - INTRADAY_BASE : -RECENT])],
        axis=1,
    )
    out = model.predict(feats)
    out["abstain_reason"] = [c.abstain_reason for c in checks]
    out["issues"] = [c.issues for c in checks]
    return out


@pytest.fixture(scope="module")
def scored() -> pd.DataFrame:
    normal = _household(1)
    dead = normal.copy()
    dead[-20:] = 0.0  # contor oprit de 20 de zile
    negative = normal.copy()
    negative[-25:] = -np.abs(negative[-25:])  # polaritate inversată
    wh = normal * 1000.0  # aceeași casă, trimisă în Wh
    short = np.full_like(normal, np.nan)
    short[-15:] = normal[-15:]  # contor montat acum 15 zile
    spiky = normal.copy()
    spiky[-3, 20] = 40.0  # o valoare imposibilă pentru un branșament casnic
    return _score([normal, dead, negative, wh, short, spiky])


def test_dead_meter_is_flagged_as_faulty(scored) -> None:
    assert scored.loc[1, "score"] > 0.8 and scored.loc[1, "label"] == "faulty"
    assert scored.loc[1, "score"] > scored.loc[0, "score"]


def test_negative_readings_are_flagged(scored) -> None:
    assert scored.loc[2, "score"] > 0.8
    assert any("negative" in i for i in scored.loc[2, "issues"])


def test_wh_input_is_converted_and_scores_like_kwh(scored) -> None:
    assert any("Wh" in i for i in scored.loc[3, "issues"])
    assert abs(scored.loc[3, "score"] - scored.loc[0, "score"]) < 1e-6


def test_short_history_abstains_with_reason(scored) -> None:
    assert scored.loc[4, "abstain_reason"] and "istoric prea scurt" in scored.loc[4, "abstain_reason"]


def test_impossible_value_is_reported_not_dropped(scored) -> None:
    assert any("branșament" in i for i in scored.loc[5, "issues"])
    assert 40.0 > MAX_KWH_PER_HALFHOUR


def test_all_missing_window_does_not_crash() -> None:
    out = check_window(np.full((180, 48), np.nan))
    assert out.abstain_reason and out.valid_days == 0


def test_infinite_values_become_missing() -> None:
    w = _household(3)
    w[-1, :5] = np.inf
    out = check_window(w)
    assert np.isnan(out.hh[-1, :5]).all() and any("infinite" in i for i in out.issues)


def test_utc_readings_are_converted_to_local_time() -> None:
    ts = pd.date_range("2026-07-01 00:00", periods=96, freq="30min", tz="UTC") + pd.Timedelta(minutes=30)
    df = pd.DataFrame({"timestamp": ts, "kwh": 0.1})
    hh, _ = readings_to_halfhours(df, "2026-07-01", "2026-07-02")
    # ora României vara = UTC+3: prima citire UTC (00:00-00:30) e la 03:00-03:30 ora locală, slotul 6
    assert np.isnan(hh[0, :6]).all() and hh[0, 6] == pytest.approx(0.1)


def test_demo_population_is_deterministic() -> None:
    a = demo.build_population(date(2025, 7, 8), "test-determinism", n_meters=300)
    b = demo.build_population(date(2025, 7, 8), "test-determinism", n_meters=300)
    np.testing.assert_array_equal(np.nan_to_num(a.hh, nan=-1), np.nan_to_num(b.hh, nan=-1))
    pd.testing.assert_frame_equal(a.meters, b.meters)


def test_missing_profile_source_fails_with_clear_message(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(demo, "HH_NPY", tmp_path / "nu-exista.npy")
    with pytest.raises(SystemExit, match="make a-data"):
        demo.profile_source(pd.Timestamp("2013-03-03"))  # înaintea perioadei din pachetul demo
