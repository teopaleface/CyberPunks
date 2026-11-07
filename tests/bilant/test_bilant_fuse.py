"""Fuziunea bilanț + A: confirmare, infirmare, lucrări neatinse, contracte valide."""

from __future__ import annotations

import json

import pytest

from cyberpunks.a_bilant import fuse
from cyberpunks.common.contracts import BilantFusion, WorkItem
from cyberpunks.common.paths import CONTRACTS


def test_combine_confirms_and_refutes():
    up, lr_up = fuse.combine(0.5, excess_kwh=8.0, sigma_kwh=2.0, meter_deficit_kwh=8.0)
    down, lr_down = fuse.combine(0.5, excess_kwh=0.0, sigma_kwh=2.0, meter_deficit_kwh=8.0, demote=True)
    kept, lr_kept = fuse.combine(0.5, excess_kwh=0.0, sigma_kwh=2.0, meter_deficit_kwh=8.0)
    same, lr0 = fuse.combine(0.5, excess_kwh=5.0, sigma_kwh=2.0, meter_deficit_kwh=0.0)
    assert up > 0.8 and lr_up > 0
    assert down < 0.2 and lr_down < 0
    assert kept == pytest.approx(0.5) and lr_kept == 0.0  # implicit: bilanțul doar confirmă
    assert same == pytest.approx(0.5) and lr0 == pytest.approx(0.0)
    assert abs(lr_up) <= fuse.LOG_LR_CAP and abs(lr_down) <= fuse.LOG_LR_CAP


@pytest.fixture
def items_and_state(tmp_path, monkeypatch):
    items = [WorkItem.model_validate(json.loads(x)) for x in (CONTRACTS / "fixtures" / "work_items_A.jsonl").read_text().splitlines() if x.strip()]
    first = items[0].model_dump(mode="json")
    first["extra"]["post_id"] = "PT-9999"
    first["extra"]["estimated_kwh_lost_per_day"] = 6.0
    items[0] = WorkItem.model_validate(first)
    state = {"loss_cost_lei_per_kwh": 0.7, "posts": {"PT-9999": {"lat": 44.43, "lon": 26.02, "excess_kwh_day": 6.5, "sigma_kwh_day": 1.5, "prediction_id": "p-1", "has_balance": True}}}
    monkeypatch.setattr(fuse, "state_path", lambda s, d: tmp_path / "state.json")
    (tmp_path / "state.json").write_text(json.dumps(state))
    return items


def test_fuse_updates_meter_items_only(items_and_state):
    items = items_and_state
    out = fuse.fuse(items, "demo-vara", "2025-07-08")
    assert len(out) == len(items)
    w = out[0]
    f = BilantFusion.model_validate(w.extra["fusion"])
    assert f.combined_score == pytest.approx(w.prediction.score)
    assert w.prediction.score > items[0].prediction.score
    assert w.impact.expected_value_lei == pytest.approx(round(w.prediction.score * w.impact.value_if_true_lei, 2))
    assert "Confirmat" in w.explanation.summary_ro
    assert w.extra["fusion_approx_post"] is False
    for x in out:
        WorkItem.model_validate(x.model_dump(mode="json"))
    # a doua aplicare nu schimbă nimic
    again = fuse.fuse(out, "demo-vara", "2025-07-08")
    assert again[0].prediction.score == w.prediction.score


def test_fuse_without_state_is_identity(tmp_path, monkeypatch):
    monkeypatch.setattr(fuse, "state_path", lambda s, d: tmp_path / "nope.json")
    items = [WorkItem.model_validate(json.loads(x)) for x in (CONTRACTS / "fixtures" / "work_items_A.jsonl").read_text().splitlines() if x.strip()]
    assert fuse.fuse(items, "demo-vara", "2025-07-08") == items


def test_unknown_post_keeps_a_score(items_and_state):
    items = items_and_state
    data = items[1].model_dump(mode="json")
    data["extra"]["post_id"] = "PT-0001"  # post din afara registrului
    data["extra"]["estimated_kwh_lost_per_day"] = 6.0
    w = fuse.fuse([WorkItem.model_validate(data)], "demo-vara", "2025-07-08")[0]
    assert w.prediction.score == pytest.approx(items[1].prediction.score)
    assert w.extra["fusion_approx_post"] is True


def test_strong_confirmation_resolves_abstain(items_and_state, monkeypatch):
    monkeypatch.setattr(fuse, "RESOLVE_ABSTAIN", True)
    items = items_and_state
    data = items[0].model_dump(mode="json")
    data["prediction"].update({"abstain": True, "abstain_reason": "test", "confidence": "low", "score": 0.5, "interval_low": 0.3, "interval_high": 0.7})
    data["recommended_action"] = "human_review"
    w = fuse.fuse([WorkItem.model_validate(data)], "demo-vara", "2025-07-08")[0]
    assert not w.prediction.abstain and w.recommended_action.value == "remote_reading"
    assert w.extra["fusion_resolved_abstain"] is True


def test_abstain_stays_with_human_by_default(items_and_state):
    data = items_and_state[0].model_dump(mode="json")
    data["prediction"].update({"abstain": True, "abstain_reason": "test", "confidence": "low", "score": 0.5, "interval_low": 0.3, "interval_high": 0.7})
    data["recommended_action"] = "human_review"
    w = fuse.fuse([WorkItem.model_validate(data)], "demo-vara", "2025-07-08")[0]
    assert w.prediction.abstain and w.recommended_action.value == "human_review"
