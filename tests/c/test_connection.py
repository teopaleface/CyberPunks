"""Cererile de racordare: intrări greșite, post deja peste limită, aprobare, aprobare cu limită de injecție."""

from __future__ import annotations

import pytest

from cyberpunks.c_prosumatori.connection import assess

VALID = {"aprobat", "aprobat_cu_limita", "studiu"}


def test_wrong_inputs_are_rejected_with_reason() -> None:
    assert assess("PT-1001", -5)["decision"] == "respins_intrare"
    assert assess("PT-1001", 0)["decision"] == "respins_intrare"
    assert assess("PT-9999", 10)["decision"] == "respins_intrare"


def test_small_request_on_quiet_post_is_approved() -> None:
    d = assess("PT-1001", 6)
    assert d["decision"] == "aprobat"
    assert d["p90_ref_after_pu"] < 1.10 and d["physics_vmax_ref_after_pu"] < 1.10
    assert "1,10" in d["explanation_ro"] and d["synthetic"]


def test_post_already_over_goes_to_study() -> None:
    d = assess("PT-1047", 10)
    assert d["decision"] == "studiu" and d["rule_id"] == "C-RAC-3-POST-DEJA-PESTE"


@pytest.mark.parametrize("post_id,kwp", [("PT-1266", 25.0), ("PT-1020", 10.0)])
def test_limit_is_physically_consistent(post_id: str, kwp: float) -> None:
    d = assess(post_id, kwp)
    assert d["decision"] in VALID
    if d["decision"] == "aprobat_cu_limita":
        assert 0.0 <= d["export_limit_kw"] < kwp
    # mai mulți kW nu pot coborî tensiunea estimată
    assert d["p90_ref_after_pu"] >= d["p90_ref_before_pu"] - 1e-3
