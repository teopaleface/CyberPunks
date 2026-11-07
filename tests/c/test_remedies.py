"""Scara de soluții: formulele, echivalența prizei cu rețeaua reconstruită, alegerea combinației, contractul."""

from __future__ import annotations

import copy
from datetime import date

import numpy as np
import pandas as pd
import pytest

from cyberpunks.c_prosumatori import grids, posts, remedies, weather
from cyberpunks.common.contracts import RemedyOption


def test_unbalance_factor_limits() -> None:
    assert remedies.unbalance_factor(np.array([1.0, 1.0, 1.0])) == pytest.approx(1.0)
    assert remedies.unbalance_factor(np.array([1.0, 0.0, 0.0]), rho=1.0) == pytest.approx(6.0)
    assert remedies.unbalance_factor(np.array([1.0, 0.0, 0.0]), rho=0.0) == pytest.approx(3.0)
    assert remedies.unbalance_factor(np.array([0.0, 0.0, 0.0])) == 1.0
    # mai echilibrat înseamnă factor mai mic
    assert remedies.unbalance_factor(np.array([0.5, 0.3, 0.2])) > remedies.unbalance_factor(np.array([0.36, 0.33, 0.31]))


def _opt(action: str, cost: float, effect: float, conf: str = "high", combinable: bool = True) -> dict:
    return {"action": action, "cost_lei": cost, "effect_pu": effect, "p90_after_pu": 1.13 + effect, "confidence": conf,
            "combinable": combinable}


def test_choose_cheapest_effective_single_and_pair() -> None:
    opts = [_opt("notify_customers", 3, -0.002, "low"), _opt("phase_rebalance", 300, -0.018, "low"), _opt("adjust_tap", 1600, -0.024),
            _opt("export_limit", 9000, -0.04, "medium"), _opt("transformer_upgrade", 80000, -0.05)]
    acts, reason, ok = remedies.choose(opts, 1.13)
    assert ok and acts == ["phase_rebalance", "adjust_tap"]  # 1.13 - 0.042 = 1.088 < 1.098, mai ieftin decât exportul
    assert "mesaje de grup" in reason  # spune de ce nu treapta mai ieftină
    acts, _, ok = remedies.choose(opts[:3], 1.20)  # nimic nu ajunge: cea mai bună variantă, post în investiții
    assert not ok and "adjust_tap" in acts


def test_low_confidence_alone_is_not_enough() -> None:
    opts = [_opt("notify_customers", 3, -0.05, "low"), _opt("offer_battery", 10, -0.05, "low")]
    acts, _, ok = remedies.choose(opts, 1.12)
    assert not ok or any(a not in ("notify_customers", "offer_battery") for a in acts)


@pytest.fixture(scope="module")
def demo_day() -> remedies.Day:
    d = date(2025, 7, 8)
    start = pd.Timestamp(d, tz="Europe/Bucharest").tz_convert("UTC") + pd.Timedelta(hours=1)
    wx = weather.archive().reindex(pd.date_range(start, periods=24, freq="h"))
    return remedies.day_inputs(d, wx)


def test_tap_shortcut_matches_rebuilt_network(demo_day: remedies.Day) -> None:
    """Priza simulată prin tensiunea pe MT împărțită la raportul treptelor dă aceeași tensiune ca rețeaua refăcută."""
    pid = posts.load_posts().sort_values("pv_kw_per_kva", ascending=False).post_id.iloc[0]
    post = remedies.get_post(pid)
    if post.spec.tap_pos >= 2:
        pytest.skip("priza e deja la capăt")
    base = remedies.run_sim(post, demo_day)
    vm = base.detail["vm"]
    k = (1 + 0.025 * post.spec.tap_pos) / (1 + 0.025 * (post.spec.tap_pos + 1))
    fast = remedies.run_sim(post, demo_day, vm=vm * k)
    spec = copy.deepcopy(post.spec)
    spec.tap_pos += 1
    slow = remedies.run_sim(grids.build_post(spec), demo_day, vm=vm)
    assert np.max(np.abs(fast.vmax_h - slow.vmax_h)) < 5e-4
    assert fast.vmax < base.vmax


def test_ladder_options_follow_contract(demo_day: remedies.Day) -> None:
    pid = posts.load_posts().sort_values("pv_kw_per_kva", ascending=False).post_id.iloc[0]
    lad = remedies.build_ladder(pid, demo_day, p90_model=1.13, n_customers=100, horizon_days=55)
    acts = [o["action"] for o in lad.options]
    assert "adjust_tap" in acts or remedies.get_post(pid).spec.tap_pos >= 2
    assert {"phase_rebalance", "notify_customers", "transformer_upgrade"} <= set(acts)
    for o in lad.options:
        RemedyOption.model_validate(o)
        assert o["p90_after_pu"] == pytest.approx(lad.p90_start + o["effect_pu"], abs=1e-3)
        assert o["effect_pu"] <= 1e-3  # nicio treaptă nu urcă tensiunea
    notify = next(o for o in lad.options if o["action"] == "notify_customers")
    assert notify["participation_rate"] == pytest.approx(0.1) and notify["message_preview_ro"]


def test_shift_is_energy_neutral_and_never_negative() -> None:
    rng = np.random.default_rng(0)
    load = rng.uniform(0.0, 0.6, (12, 24))
    load[3, 18:22] = 0.05  # o casă care consumă foarte puțin seara
    hours = np.arange(24)
    risk, eve = (hours >= 11) & (hours < 15), (hours >= 18) & (hours < 22)
    extra = remedies.shift_profile(load, risk, eve, kwh=1.5)
    assert np.allclose(extra.sum(axis=1), 0.0)  # energia doar se mută
    assert (load + extra >= -1e-12).all()  # consumul nu devine negativ
    assert extra[:, risk].sum() > 0 and extra[3].sum() == pytest.approx(0.0)
    # orele care sunt și cu risc, și de seară nu se dublează
    both = remedies.shift_profile(load, hours >= 10, hours >= 12, kwh=1.0)
    assert np.allclose(both.sum(axis=1), 0.0)


def test_negative_margin_never_crosses_quantiles() -> None:
    from cyberpunks.c_prosumatori import features as F
    from cyberpunks.c_prosumatori import train as T

    b = T.load_bundle()
    d = date(2025, 7, 8)
    start = pd.Timestamp(d, tz="Europe/Bucharest").tz_convert("UTC") + pd.Timedelta(hours=1)
    hw = F.hourly_weather(weather.archive().reindex(pd.date_range(start, periods=24, freq="h")))
    st = posts.load_posts().iloc[0]
    b.hourly.cqr_margin = -0.05
    p = b.hourly.predict(F.hourly_features(st, hw))
    assert (p["q10"] <= p["q50"] + 1e-12).all() and (p["q50"] <= p["q90"] + 1e-12).all()


def test_window_ending_at_midnight() -> None:
    from cyberpunks.c_prosumatori.predict import _window_end

    end = _window_end(date(2025, 7, 8), 24)
    assert (end.year, end.month, end.day, end.hour, end.minute) == (2025, 7, 9, 0, 0)


def test_widen_never_crosses_median() -> None:
    from cyberpunks.c_prosumatori.train import widen

    q10, q50, q90 = np.array([1.04]), np.array([1.05]), np.array([1.06])
    lo, hi = widen(q10, q50, q90, 0.01)
    assert lo[0] == pytest.approx(1.03) and hi[0] == pytest.approx(1.07)
    lo, hi = widen(q10, q50, q90, -0.02)  # strângere prea mare: se oprește la P50
    assert lo[0] == pytest.approx(1.05) and hi[0] == pytest.approx(1.05)
