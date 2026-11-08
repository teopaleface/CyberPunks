"""Cap-coadă pentru lucrările C (offline): contractul, scara de soluții și textele în română."""

from __future__ import annotations

import json
import re
import shutil

import pytest

from cyberpunks.c_prosumatori import predict
from cyberpunks.common.contracts import RemedyOption, Series, WorkItem
from cyberpunks.common.paths import OUTPUTS

SCENARIO = "test-c-cap-coada"
DOT_DECIMAL = re.compile(r"\d\.(\d{1,2}|\d{4,})(?!\d)")  # 0.020, 2.2 (punct zecimal); 15.000 (mii) e corect


@pytest.fixture(scope="module")
def items():
    path = predict.run(SCENARIO, "2025-07-08")
    out = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    yield out
    shutil.rmtree(OUTPUTS / "work_items" / SCENARIO, ignore_errors=True)
    shutil.rmtree(OUTPUTS / "series" / SCENARIO, ignore_errors=True)


def _texts(it: dict) -> list[str]:
    e = it["extra"]
    t = [it["explanation"]["summary_ro"], e.get("ladder_reason_ro") or "", e.get("customer_message_ro") or "", e.get("outage_notice_ro") or ""]
    t += [f["label_ro"] for f in it["explanation"]["top_factors"]]
    t += [o["note_ro"] + " " + (o.get("message_preview_ro") or "") for o in e.get("remedy_options", [])]
    return t


def test_work_items_follow_contract(items: list[dict]) -> None:
    assert items, "ziua demo trebuie să aibă lucrări C"
    for it in items:
        WorkItem.model_validate(it)
        series = OUTPUTS / "series" / SCENARIO / f"{it['work_item_id']}.json"
        Series.model_validate_json(series.read_text(encoding="utf-8"))
        # carantina planificatorului: valoarea așteptată = scor × valoare (abatere sub 2%)
        im, p = it["impact"], it["prediction"]["score"]
        assert abs(im["expected_value_lei"] - p * im["value_if_true_lei"]) <= 0.02 * max(im["expected_value_lei"], 1.0)


def test_ladder_fields_present(items: list[dict]) -> None:
    ladders = [it for it in items if it["extra"].get("remedy_options")]
    assert ladders, "pe 8 iulie 2025 cel puțin un post are scara de soluții"
    for it in ladders:
        e = it["extra"]
        assert e["ladder_base_p90_pu"] >= it["prediction"]["point_interval"][1] - 1e-9  # interfața pornește scara de aici
        for o in e["remedy_options"]:
            RemedyOption.model_validate(o)


def test_texts_use_romanian_decimals_and_no_absolute_probability(items: list[dict]) -> None:
    for it in items:
        for t in _texts(it):
            m = DOT_DECIMAL.search(t)
            assert m is None, f"{it['asset_id']}: zecimală cu punct în „…{t[max(0, m.start() - 25):m.end() + 5]}…”"
        assert "100%" not in it["explanation"]["summary_ro"] and " 0%" not in it["explanation"]["summary_ro"]
