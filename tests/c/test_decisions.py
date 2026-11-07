"""Regulile de decizie C și verificările de intrare (robustețe: intrări greșite, rețele noi, prognoză nesigură)."""

from __future__ import annotations

from datetime import date

import pandas as pd

from cyberpunks.c_prosumatori import actions
from cyberpunks.c_prosumatori.predict import check_post, ood_reasons

BASE = {"q10": 1.10, "q50": 1.12, "q90": 1.13, "lost_kwh": 60.0, "n_prosumers": 40, "n_customers": 100, "tap_pos": 0,
        "q50_after_tap": 1.095, "target": date(2025, 7, 8), "issues_block": [], "ood_reasons": [], "weather_uncertain": False}


def _post(**kw) -> pd.Series:
    r = {"kva": 250.0, "n_customers": 100, "n_prosumers": 30, "pv_kw": 200.0, "pv_kw_per_kva": 0.8, "prosumer_share": 0.3,
         "battery_kwh": 50.0, "battery_pv_share": 0.3, "annual_load_mwh": 250.0, "line_km": 1.5, "max_path_km": 0.5,
         "r_max_ohm": 0.2, "sens_pv_pu": 0.08, "sens_load_pu": 0.01, "vk_percent": 6.0, "tap_pos": 0, "v0_est": 1.03,
         "vm_mv_est": 1.03, "lat": 44.45, "lon": 26.05}
    r.update(kw)
    return pd.Series(r)


def test_high_risk_high_value_recommends_tap() -> None:
    d = actions.decide(p=0.97, **{**BASE, "lost_kwh": 120.0})
    assert d.action == "adjust_tap" and d.requires_outage and d.rule_id == "C-R4-PRIZA"


def test_tap_at_limit_goes_to_measurement_and_investment() -> None:
    d = actions.decide(p=0.97, **{**BASE, "tap_pos": 2})
    assert d.action == "measurement_campaign" and d.investment_flag


def test_measurement_only_when_value_covers_its_cost() -> None:
    # depășire probabilă, priza nu se justifică (întreruperea costă), dar valoarea acoperă 300 lei de măsurători
    d = actions.decide(p=0.9, **{**BASE, "lost_kwh": 30.0})
    assert d.action == "measurement_campaign"
    # valoare mică: nici măsurători, doar mesaj către prosumatori
    d = actions.decide(p=0.9, **{**BASE, "lost_kwh": 2.0, "n_prosumers": 5})
    assert d.action == "notify_customers"
    # în noiembrie, aceeași depășire valorează mai puțin (puține zile senine rămase)
    d = actions.decide(p=0.9, **{**BASE, "lost_kwh": 30.0, "target": date(2026, 11, 8)})
    assert d.action == "notify_customers"


def test_small_risk_notifies_and_negligible_risk_is_dropped() -> None:
    assert actions.decide(p=0.08, **{**BASE, "q10": 1.07, "q50": 1.08, "q90": 1.09}).action == "notify_customers"
    assert actions.decide(p=0.001, **{**BASE, "q10": 1.02, "q50": 1.03, "q90": 1.05}) is None


def test_invalid_input_abstains_to_human() -> None:
    d = actions.decide(p=0.9, **{**BASE, "issues_block": ["puterea transformatorului e 0 kVA"]})
    assert d.abstain and d.action == "human_review" and "0 kVA" in d.abstain_reason


def test_new_network_abstains() -> None:
    d = actions.decide(p=0.9, **{**BASE, "ood_reasons": ["kW de panouri pe kVA = 5, antrenat pe 0-3,2"]})
    assert d.abstain and d.rule_id == "C-R2-RETEA-NOUA"


def test_uncertain_forecast_near_limit_goes_to_human() -> None:
    d = actions.decide(p=0.5, **{**BASE, "q10": 1.09, "q50": 1.10, "q90": 1.12, "weather_uncertain": True})
    assert d.abstain and d.rule_id == "C-R3-PROGNOZA-INCERTA"


def test_check_post_catches_wrong_inputs() -> None:
    assert check_post(_post())[0] == []
    assert any("kVA" in x for x in check_post(_post(kva=0.0))[0])
    assert any("negativă" in x for x in check_post(_post(pv_kw=-50.0))[0])
    assert any("prosumatori" in x for x in check_post(_post(n_prosumers=500))[0])
    assert any("coordonate" in x for x in check_post(_post(lat=47.0))[0])
    block, fixed = check_post(_post(battery_kwh=float("nan")))
    assert block == [] and fixed


def test_ood_flags_networks_outside_training() -> None:
    ranges = {k: [0.0, 1.0] for k in ["pv_kw_per_kva", "sens_pv_pu", "r_max_ohm", "max_path_km", "battery_pv_share"]}
    ranges.update({"v0_est": [0.98, 1.08], "kva": [100, 630], "pv_kw": [0, 900]})
    assert ood_reasons(_post(), ranges) == []
    assert ood_reasons(_post(pv_kw_per_kva=4.0), ranges)


def test_season_horizon_and_working_days() -> None:
    assert actions.season_horizon_days(date(2025, 7, 8)) > actions.season_horizon_days(date(2025, 11, 9))
    assert actions.add_working_days(date(2025, 7, 4), 2) == date(2025, 7, 8)  # vineri + 2 zile lucrătoare = marți
    assert "Ore Smart+" in actions.customer_message(date(2025, 7, 8), 10, (11, 15))
    assert "Ore Smart+" not in actions.customer_message(date(2026, 11, 9), 10, (11, 15))
