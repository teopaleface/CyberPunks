"""Lucrările A trec contractul și regulile de carantină ale planificatorului (rulează din pachetul demo din git)."""

from __future__ import annotations

import json
from datetime import date

import pytest

from cyberpunks.a_contoare.predict import run
from cyberpunks.common.config import load
from cyberpunks.common.contracts import Series, WorkItem
from cyberpunks.common.paths import ROOT


@pytest.fixture(scope="module")
def demo_items() -> tuple[list[WorkItem], str]:
    path = run("demo-vara", None)
    items = [WorkItem.model_validate_json(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return items, str(load("scenarios")["scenarios"]["demo-vara"]["date"])


def test_items_exist_and_valid(demo_items) -> None:
    items, _ = demo_items
    assert 50 <= len(items) <= 300
    assert all(w.source.value == "A" and w.kind.value == "meter_inspection" for w in items)


def test_quarantine_rules_of_planner(demo_items) -> None:
    items, plan_date = demo_items
    bbox = load("area")["demo_bbox_bucuresti_ilfov"]
    for w in items:
        assert w.target_date == date.fromisoformat(plan_date)
        assert w.work_item_id == f"A-{w.target_date:%Y%m%d}-{w.asset_id}"
        assert bbox["lat_min"] <= w.location.lat <= bbox["lat_max"]
        assert bbox["lon_min"] <= w.location.lon <= bbox["lon_max"]
        expected = w.prediction.score * w.impact.value_if_true_lei
        assert abs(w.impact.expected_value_lei - expected) <= 0.02 * max(expected, 1.0)
        assert w.prediction.interval_low <= w.prediction.score <= w.prediction.interval_high


def test_abstain_goes_to_human_with_reason(demo_items) -> None:
    items, _ = demo_items
    abstained = [w for w in items if w.prediction.abstain]
    assert abstained, "trebuie să existe cazuri 'nu sunt sigur' (istoric scurt, zona gri)"
    for w in abstained:
        assert w.recommended_action.value == "human_review" and w.prediction.abstain_reason


def test_explanations_are_plain_words(demo_items) -> None:
    items, _ = demo_items
    for w in items:
        assert w.explanation.top_factors and w.explanation.summary_ro
        assert all("fără valoare" not in f.label_ro for f in w.explanation.top_factors)
        assert w.data_quality.synthetic is True


def test_series_written_for_each_item(demo_items) -> None:
    items, _ = demo_items
    for w in items[:30]:
        p = ROOT / w.extra["series_ref"]
        s = Series.model_validate_json(p.read_text(encoding="utf-8"))
        assert s.work_item_id == w.work_item_id and s.synthetic


def test_summary_counts(demo_items) -> None:
    items, _ = demo_items
    summary = json.loads((ROOT / "outputs/work_items/demo-vara/A_summary.json").read_text(encoding="utf-8"))
    assert summary["meters_scored"] == 10_000 and summary["work_items"] == len(items)
