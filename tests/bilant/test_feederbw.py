"""Date reale: convenția orei, completare din trecut și separare pe sursă."""

import numpy as np
import pandas as pd
import pytest

from cyberpunks.a_bilant import dataset, feederbw


def test_hour_alignment_and_causal_gaps():
    ts = pd.date_range("2024-01-01", periods=10 * 24 * 60, freq="min", tz="UTC")
    power = np.full(len(ts), 10.0)
    # O valoare viitoare de 99 kW nu trebuie să umple golul de acum 7 zile.
    power[168 * 60:169 * 60] = np.nan
    power[169 * 60:170 * 60] = 99.0
    power[170 * 60:171 * 60] = -2.0
    frame = pd.DataFrame({"timestamp_UTC": ts, "active_power_kW": power})
    index = pd.date_range("2024-01-01 01:00", periods=240, freq="h", tz="UTC")
    shape, quality = feederbw.hourly_import(frame, index)
    assert shape[168] == 10.0
    assert shape[169] == 99.0
    assert shape[170] == 0.0
    assert quality["missing_hours"] == 1
    assert quality["export_hours_clipped"] == 1
    # Un gol la început nu se completează cu informație din viitor.
    frame.loc[:59, "active_power_kW"] = np.nan
    with pytest.raises(ValueError, match="Prima oră"):
        feederbw.hourly_import(frame, index)


def test_source_and_neighbors_never_cross_splits():
    _, meta = dataset.train_specs()
    mapping = feederbw.source_assignment(meta, list(range(1, 41)))
    split = feederbw.feeder_split(list(range(1, 41)))
    reverse = {f: name for name, feeders in split.items() for f in feeders}
    assert sum(map(len, split.values())) == len(reverse) == 40
    assert [len(split[k]) for k in ("train", "validation", "test")] == [24, 8, 8]
    for post, neighbors in dataset.neighbors(meta).items():
        assert all(reverse[mapping[post]] == reverse[mapping[q]] for q in neighbors)
