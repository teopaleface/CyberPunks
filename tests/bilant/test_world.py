"""Testele simulatorului bilanțului (fără descărcări: meteo construit în test)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from cyberpunks.a_bilant import problems as P
from cyberpunks.a_bilant import world


def test_phase_multiplier_balanced_vs_unbalanced():
    bal = world.phase_multiplier((1 / 3, 1 / 3, 1 / 3), 100)
    unb = world.phase_multiplier((0.6, 0.25, 0.15), 100)
    assert bal == pytest.approx(1 + 1.09 * 6 / (0.18 * 100))
    assert unb > bal * 1.5
    assert world.unbalance_u((0.6, 0.25, 0.15)) == pytest.approx(0.8)


@pytest.mark.parametrize("kind", ["zero", "stuck", "negative", "h1", "bypass"])
def test_meter_problem_only_after_onset(kind):
    x = np.linspace(0.2, 1.0, 96)
    day = np.repeat(np.arange(4), 24)
    on = day >= 2
    params = {"type": kind, "s": 1.0, "seed": 1, "alpha": 0.5, "p": 0.5, "ramp_days": 1}
    y = P.apply_meter_problem(x, on, params, day)
    assert np.allclose(y[~on], x[~on])
    assert y[on].sum() < x[on].sum()  # toate tipurile ascund consum (stuck: valoarea dinainte e mai mică aici)


def _tiny_weather(days: int = 6) -> world.Weather:
    from cyberpunks.c_prosumatori import profiles

    idx = pd.date_range("2025-06-01 22:00", periods=days * 24, freq="h", tz="UTC") + pd.Timedelta(hours=1)
    h = (idx.tz_convert(world.TZ) - pd.Timedelta(hours=1)).hour.to_numpy()
    gti = np.clip(np.sin((h - 6) / 14 * np.pi), 0, None) * 800
    loc = pd.DatetimeIndex((idx.tz_convert(world.TZ) - pd.Timedelta(hours=1)).date)
    days_idx = pd.DatetimeIndex(sorted(set(loc)))
    return world.Weather(idx, gti, np.full(len(idx), 25.0), profiles.shapes_for(idx), profiles.system_load_index(idx), days_idx.get_indexer(loc), days_idx)


@pytest.fixture(scope="module")
def tiny():
    from cyberpunks.c_prosumatori import grids

    wx = _tiny_weather()
    spec = grids.sample_spec("rural1", np.random.default_rng(4), "T-rural1", mode="population")
    return wx, spec


def test_balance_identity_and_determinism(tiny):
    wx, spec = tiny
    plan = P.PostPlan("T-rural1", (0.34, 0.33, 0.33), [])
    a = world.simulate(spec, wx, plan)
    b = world.simulate(spec, wx, plan)
    assert np.array_equal(a.balance_kwh, b.balance_kwh)
    short = a.balance_kwh.sum() - np.nansum(a.cust_kwh)
    true = a.true_line_loss_kwh.sum() + a.true_own_kwh * wx.T
    assert short == pytest.approx(true, rel=0.25, abs=1.0)  # erori de contor și goluri mici
    assert (a.true_line_loss_kwh >= 0).all()


def test_theft_and_config_show_in_balance(tiny):
    wx, spec = tiny
    base = world.simulate(spec, wx, P.PostPlan("T", (0.34, 0.33, 0.33), []))
    theft = world.simulate(spec, wx, P.PostPlan("T", (0.34, 0.33, 0.33), [P.Problem("theft_before_meter", 3, 0, {"kw": 1.0, "shape": "constant", "near_customer": 1})]))
    on = wx.local_day >= 3
    extra = theft.balance_kwh[on].sum() - base.balance_kwh[on].sum()
    assert extra == pytest.approx(on.sum() * 1.0, rel=0.1)
    assert np.allclose(theft.balance_kwh[~on], base.balance_kwh[~on])
    cfg = world.simulate(spec, wx, P.PostPlan("T", (0.34, 0.33, 0.33), [P.Problem("balance_meter_config", 3, -1, {"factor": 2.0})]))
    assert cfg.balance_kwh[on].sum() == pytest.approx(2 * base.balance_kwh[on].sum())
