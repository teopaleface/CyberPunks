"""Protecții împotriva scurgerii etichetelor și a zilelor incomplete în testul real."""
import numpy as np
import pandas as pd

from cyberpunks.benchmark.tensiune_reala import FEATURES, aggregate, split, supervised


def days(n=30, feeders=1):
    return pd.concat([pd.DataFrame({"date": pd.date_range("2023-01-01", periods=n, tz="UTC"),
                                   "feeder": f, "v_max": 240. + np.arange(n) / 100,
                                   "v_mean": 235., "v_min": 230., "v_std": 1.})
                      for f in range(feeders)], ignore_index=True)


def test_future_readings_cannot_change_past_features():
    original = days()
    before = supervised(original)
    changed = original.copy()
    changed.loc[changed.date >= "2023-01-20", "v_max"] = 280
    after = supervised(changed)
    old = before.date < "2023-01-20"
    pd.testing.assert_frame_equal(before.loc[old, FEATURES], after.loc[old, FEATURES])
    assert before.loc[before.date == "2023-01-19", "target"].item() != after.loc[old, "target"].iloc[-1]
    assert (before.target_date - before.date).eq(pd.Timedelta(days=1)).all()


def test_missing_day_is_not_bridged_or_imputed():
    frame = days()
    frame = frame[frame.date != "2023-01-15"]
    out = supervised(frame)
    assert not out.date.between("2023-01-14", "2023-01-21").any()


def test_split_has_disjoint_feeders_and_chronological_targets():
    parts, _ = split(supervised(days(820, 40)))
    tr, va, te = (parts[k] for k in ("train", "validation", "test"))
    assert set(tr.feeder).isdisjoint(va.feeder)
    assert set(tr.feeder).isdisjoint(te.feeder)
    assert set(va.feeder).isdisjoint(te.feeder)
    assert tr.target_date.max() < va.target_date.min() <= va.target_date.max() < te.target_date.min()


def test_repeated_minutes_cannot_fake_complete_day():
    t = pd.date_range("2023-01-01", periods=100, freq="min", tz="UTC")
    frame = pd.DataFrame({"timestamp_UTC": list(t) * 15, "voltage_one_phase_V": 235.})
    out, quality = aggregate(frame, 1)
    assert out.empty and quality["duplicate_timestamps"] == 1400


def test_full_day_keeps_actual_high_voltage_label():
    frame = pd.DataFrame({"timestamp_UTC": pd.date_range("2023-01-01", periods=1440, freq="min", tz="UTC"),
                          "voltage_one_phase_V": 235.})
    frame.loc[700, "voltage_one_phase_V"] = 260
    out, quality = aggregate(frame, 1)
    assert out.v_max.item() == 260 and quality["excluded_days"] == 0
