"""Teste pentru generatorul de defecte și furturi (date sintetice)."""

import json

import numpy as np
import pytest

from cyberpunks.a_contoare import inject as inj

ALL_KINDS = inj.FAULT_KINDS + inj.TAMPER_KINDS + inj.BENIGN_KINDS
START = 40


def make_hh(n_days: int = 120, seed: int = 0) -> np.ndarray:
    """Gospodărie sintetică: sinus zilnic + zgomot, totul pozitiv."""
    r = np.random.default_rng(seed)
    t = np.arange(48)
    prof = 0.4 + 0.3 * np.sin(2 * np.pi * (t - 12) / 48)
    return np.clip(prof[None, :] * r.uniform(0.9, 1.1, (n_days, 48)), 0.05, None)


@pytest.mark.parametrize("kind", ALL_KINDS)
def test_basic_properties(kind):
    hh = make_hh()
    orig = hh.copy()
    a, ia = inj.inject(hh, kind, np.random.default_rng(1), START)
    b, ib = inj.inject(hh, kind, np.random.default_rng(1), START)
    assert a.shape == hh.shape
    np.testing.assert_array_equal(hh, orig)  # intrarea nu e modificată
    np.testing.assert_array_equal(a, b)  # determinism
    assert ia == ib
    np.testing.assert_array_equal(a[:START], hh[:START])
    assert ia.family == inj.KIND_FAMILY[kind]
    assert START <= ia.start_day < ia.end_day <= hh.shape[0]
    assert kind in inj.KIND_LABEL_RO and kind in inj.KIND_OUTCOME


def test_none_and_families():
    hh = make_hh()
    out, info = inj.inject(hh, "none", np.random.default_rng(0), 5)
    np.testing.assert_array_equal(out, hh)
    assert out is not hh
    assert (info.kind, info.family, info.start_day, info.end_day) == ("none", "normal", -1, -1)
    assert all(inj.KIND_FAMILY[k] == "faulty" for k in inj.FAULT_KINDS)
    assert all(inj.KIND_FAMILY[k] == "tamper" for k in inj.TAMPER_KINDS)
    assert all(inj.KIND_FAMILY[k] == "normal" for k in inj.BENIGN_KINDS)


def test_zero_and_stuck():
    hh = make_hh()
    z, _ = inj.inject(hh, "zero", np.random.default_rng(0), START)
    assert (z[START:] == 0.0).all()
    s, _ = inj.inject(hh, "stuck", np.random.default_rng(0), START)
    assert np.unique(s[START:]).size == 1
    assert s[START, 0] == hh[START - 1, 47]


def test_h1_ratio():
    hh = make_hh()
    out, info = inj.inject(hh, "h1", np.random.default_rng(0), START, alpha=0.5)
    assert info.kwh_recorded / info.kwh_true == pytest.approx(0.5)
    np.testing.assert_allclose(out[START:], hh[START:] * 0.5)


@pytest.mark.parametrize("kind", ["h4", "h6"])
def test_total_preserved(kind):
    hh = make_hh()
    out, _ = inj.inject(hh, kind, np.random.default_rng(0), START)
    np.testing.assert_allclose(out[START:].sum(axis=1), hh[START:].sum(axis=1))
    if kind == "h4":
        assert np.allclose(out[START:].std(axis=1), 0.0)
    else:
        np.testing.assert_allclose(out[START:], hh[START:, ::-1])


def test_h3_zero_runs():
    hh = make_hh()
    out, info = inj.inject(hh, "h3", np.random.default_rng(3), START, t_i=10, d=12)
    for r in range(START, hh.shape[0]):
        best = run = 0
        for v in out[r]:
            run = run + 1 if v == 0.0 else 0
            best = max(best, run)
        assert best >= 8
    assert info.params["d"] == 12


def test_negative_and_gaps():
    hh = make_hh()
    neg, _ = inj.inject(hh, "negative", np.random.default_rng(0), START)
    assert (neg[START:] < 0).any()
    gaps, info = inj.inject(hh, "gaps", np.random.default_rng(0), START)
    assert np.isnan(gaps).any()
    assert info.end_day <= hh.shape[0]
    assert np.isfinite(gaps[:START]).all()


def test_spikes_and_drift_and_clock():
    hh = make_hh()
    sp, _ = inj.inject(hh, "spikes", np.random.default_rng(0), START)
    assert sp.max() > 3 * hh.max()
    assert sp.max() <= 50.0
    _, info = inj.inject(hh, "drift", np.random.default_rng(0), START)
    assert info.kwh_recorded < info.kwh_true
    ck, info = inj.inject(hh, "clock_drift", np.random.default_rng(0), START, k=2)
    assert info.kwh_recorded == pytest.approx(info.kwh_true, rel=0.01)
    assert not np.allclose(ck, hh)


def test_nan_preserved():
    hh = make_hh()
    hh[50, 5] = np.nan
    for kind in ("h1", "h2", "h5", "bypass", "night", "negative", "drift", "h6"):
        out, _ = inj.inject(hh, kind, np.random.default_rng(0), START)
        if kind == "h6":
            assert np.isnan(out[50, 42])
        elif kind == "night":
            assert np.isnan(out[50, 5])
        else:
            assert np.isnan(out[50, 5])


@pytest.mark.parametrize("kind", ["h1", "h2", "h3", "h5", "bypass", "night", "zero"])
def test_recorded_below_true(kind):
    hh = make_hh()
    _, info = inj.inject(hh, kind, np.random.default_rng(0), START)
    assert info.kwh_recorded < info.kwh_true


def test_vacation_and_occupancy():
    hh = make_hh()
    v, info = inj.inject(hh, "vacation", np.random.default_rng(0), START)
    assert 7 <= info.end_day - info.start_day <= 21
    assert info.kwh_recorded < info.kwh_true
    np.testing.assert_array_equal(v[info.end_day :], hh[info.end_day :])
    _, info = inj.inject(hh, "occupancy_change", np.random.default_rng(0), START, up=True)
    assert info.params["factor"] > 1.0


def test_sample_kind_probs():
    rng = np.random.default_rng(0)
    assert all(inj.sample_kind(rng, {"zero": 1.0}) == "zero" for _ in range(20))
    kinds = {inj.sample_kind(rng) for _ in range(3000)}
    assert "none" in kinds and len(kinds) > 5
    with pytest.raises(ValueError):
        inj.sample_kind(rng, {"nope": 1.0})


def test_sample_and_inject():
    hh = make_hh()
    for seed in range(30):
        out, info = inj.sample_and_inject(
            hh, np.random.default_rng(seed), min_onset_day=30, probs={k: 1.0 for k in ALL_KINDS}
        )
        assert out.shape == hh.shape
        assert info.start_day >= 30
        assert info.end_day <= hh.shape[0]
    _, info = inj.sample_and_inject(
        hh, np.random.default_rng(1), min_onset_day=30, probs={"h1": 1.0}, max_duration_days=10
    )
    assert info.end_day - info.start_day == 10
    _, info = inj.sample_and_inject(hh, np.random.default_rng(1), min_onset_day=30, probs={"h1": 1.0})
    assert info.end_day == hh.shape[0]
    _, info = inj.sample_and_inject(hh, np.random.default_rng(1), min_onset_day=30, probs={"none": 1.0})
    assert info.kind == "none"


@pytest.mark.parametrize("kind", ("none", *ALL_KINDS))
def test_to_dict_json(kind):
    hh = make_hh()
    _, info = inj.inject(hh, kind, np.random.default_rng(0), START)
    d = json.loads(json.dumps(info.to_dict()))
    assert d["kind"] == kind
