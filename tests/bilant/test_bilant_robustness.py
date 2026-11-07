"""Robustețea bilanțului: intrări greșite și date lipsă."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from cyberpunks.a_bilant import inputs
from cyberpunks.a_bilant.diagnose import decide
from cyberpunks.a_bilant.problems import CLASSES


def _series(days: int = 3, seed: int = 0) -> tuple[pd.Series, pd.Series]:
    idx = pd.date_range("2025-07-01", periods=24 * days, freq="h", tz="Europe/Bucharest")
    rng = np.random.default_rng(seed)
    cust = pd.Series(20 + 10 * np.sin(np.arange(len(idx)) / 24 * 2 * np.pi) + rng.normal(0, 1, len(idx)), index=idx)
    bal = cust * 1.04 + 0.2
    return bal, cust


def test_clean_input_unchanged():
    bal, cust = _series()
    r = inputs.clean(bal, cust)
    assert r.has_balance and not r.issues
    assert np.allclose(r.balance_kwh, bal)


def test_missing_balance_meter_goes_to_plan_b():
    _, cust = _series()
    r = inputs.clean(None, cust)
    assert not r.has_balance
    assert "planul B" in r.issues[0]
    r2 = inputs.clean(pd.Series(np.nan, index=cust.index), cust)
    assert not r2.has_balance


def test_duplicated_hours_are_dropped():
    bal, cust = _series()
    dup = pd.concat([bal, bal.iloc[:5] * 3])  # retransmisiile vin după original
    r = inputs.clean(dup, cust)
    assert r.balance_kwh.index.is_unique
    assert np.allclose(r.balance_kwh, bal)
    assert any("dublate" in x for x in r.issues)


@pytest.mark.parametrize("who", ["balance", "customers"])
def test_wh_instead_of_kwh(who):
    bal, cust = _series()
    if who == "balance":
        r = inputs.clean(bal * 1000, cust)
    else:
        r = inputs.clean(bal, cust * 1000)
    assert np.allclose(r.balance_kwh / r.customers_kwh, bal / cust)
    assert any("Wh" in x for x in r.issues)


def test_missing_hours_filled_or_day_dropped():
    bal, cust = _series(days=3)
    b = bal.copy()
    b.iloc[30:31] = np.nan  # o oră în ziua 2: completată
    b.iloc[48:60] = np.nan  # 12 ore în ziua 3: ziua scoasă
    r = inputs.clean(b, cust)
    assert r.balance_kwh.iloc[30] == pytest.approx(bal.iloc[6])
    assert len(r.usable_days) == 2
    assert any("scoase" in x for x in r.issues)


def test_reversed_polarity():
    bal, cust = _series()
    r = inputs.clean(-bal, cust, has_prosumers=False)
    assert (r.balance_kwh > 0).all()
    assert any("polaritate" in x for x in r.issues)


def test_abstain_on_tie_and_wide_interval():
    proba = pd.DataFrame([[0.05, 0.45, 0.42, 0.04, 0.02, 0.02], [0.05, 0.9, 0.02, 0.01, 0.01, 0.01], [0.9, 0.02, 0.02, 0.02, 0.02, 0.02]], columns=list(CLASSES))
    win = pd.DataFrame({"width_kwh": [10.0, 60.0, 10.0], "r_mean_kwh": [8.0, 5.0, 0.0]})
    d = decide(proba, win)
    assert d["abstain"].tolist() == [True, True, False]
    assert "egalitate" in d["abstain_reason"].iloc[0] or "50%" in d["abstain_reason"].iloc[0]
    assert "larg" in d["abstain_reason"].iloc[1]


def test_suspect_meter_prefers_clear_signs():
    from cyberpunks.a_bilant.predict import suspect_meter

    rng = np.random.default_rng(0)
    cd = rng.uniform(5, 9, (10, 120))
    cd[3, 100:] = 0.0  # contor oprit
    cd[7, 100:] = cd[7, 100:] * 0.4  # consum scăzut (de exemplu concediu), fără semn clar
    i, why, drop = suspect_meter(cd, 119, excess=7.0)
    assert i == 3 and "zero" in why and drop > 5
    cd[3, 100:] = cd[3, 99]  # contor blocat pe ultima valoare
    i, why, _ = suspect_meter(cd, 119, excess=0.5)
    assert i == 3 and "blocat" in why


def test_pair_consistency_links_donor_to_receiver():
    from cyberpunks.a_bilant.diagnose import pair_consistency

    win = pd.DataFrame(
        {
            "post_id": ["PT-X", "PT-Y", "PT-Z"],
            "day": [10, 10, 10],
            "mirror_post": ["PT-Y", "PT-X", "PT-Y"],
            "neigh_mirror_corr": [-0.8, -0.8, -0.2],
            "neigh_mirror_match": [0.9, 0.9, 0.9],
            "r_mean_kwh": [6.0, -5.8, 6.0],
        }
    )
    dec = pd.DataFrame({"label": ["contor_client", "client_post_gresit", "furt_inainte_contor"], "abstain": [True, False, False], "abstain_reason": ["x", "", ""]})
    out = pair_consistency(win, dec)
    assert out["label"].tolist() == ["client_post_gresit", "client_post_gresit", "furt_inainte_contor"]
    assert out["pair_linked"].tolist() == [True, False, False]
    assert not out["abstain"].iloc[0]


def test_martor_rule():
    from cyberpunks.a_bilant import martor
    from cyberpunks.a_bilant.diagnose import apply_martor_rule

    m = np.array([100.0, 120.0, 90.0, 110.0])
    assert martor.martor_diff(m * 1.001, m) < martor.MARTOR_DIFF_LIMIT  # 0,1%: normal
    assert martor.martor_diff(m * 2.0, m) > martor.MARTOR_DIFF_LIMIT  # cazul „2×”
    assert np.isnan(martor.martor_diff(m, np.full(4, np.nan)))
    win = pd.DataFrame({"martor_diff": [0.9, 0.001, np.nan, 0.001]})
    dec = pd.DataFrame({"label": ["normal", "contor_bilant_setat", "contor_bilant_setat", "furt_inainte_contor"], "second": ["furt_inainte_contor", "furt_inainte_contor", "normal", "normal"],
                        "p_label": [0.6, 0.7, 0.7, 0.8], "p_second": [0.3, 0.2, 0.2, 0.1], "p_problem": [0.4, 0.9, 0.9, 0.9], "abstain": [False] * 4, "abstain_reason": [""] * 4})
    out = apply_martor_rule(win, dec)
    assert out["label"].tolist() == ["contor_bilant_setat", "furt_inainte_contor", "contor_bilant_setat", "furt_inainte_contor"]
    assert out["martor_rule"].tolist() == ["diferenta_peste_clasa", "contor_balanta_confirmat", "fara_martor", "in_clasa"]


def test_display_cap_and_safety_rule():
    from cyberpunks.a_bilant.predict import pfmt, safety

    assert pfmt(1.0) == "peste 99%" and pfmt(0.995) == "peste 99%" and pfmt(0.87) == "87%"
    r = pd.Series({"p_label": 0.97, "r_mean_kwh": 30.0, "night_excess_share": 0.3})
    assert safety("furt_inainte_contor", r, False, None)[0]
    assert not safety("furt_inainte_contor", r.copy().replace({30.0: 4.0}), False, None)[0]  # pierdere mică
    assert not safety("furt_inainte_contor", r, True, None)[0]  # „nu sunt sigur”: fără marcaj de siguranță
    assert not safety("contor_client", r, False, None)[0]  # o pierdere mare nu e, singură, un risc pentru oameni
    assert safety("pierdere_tehnica", r, False, 3.4)[0] and not safety("pierdere_tehnica", r, False, 2.0)[0]
