"""Testele contractelor comune. Le rulează orchestratorul la fiecare merge."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from cyberpunks.common.contracts import AuditRecord, Plan, WorkItem, validate_file

FIX = Path(__file__).resolve().parents[1] / "contracts" / "fixtures"


@pytest.mark.parametrize("name", ["work_items_A.jsonl", "work_items_B.jsonl", "work_items_C.jsonl"])
def test_fixture_work_items_valid(name: str) -> None:
    ok, errors = validate_file(FIX / name, WorkItem)
    assert ok > 0 and not errors, errors


def test_invalid_fixture_is_rejected() -> None:
    ok, errors = validate_file(FIX / "work_items_invalid.jsonl", WorkItem)
    assert ok == 0 and errors


def test_plan_and_audit_valid() -> None:
    Plan.model_validate_json((FIX / "plan_example.json").read_text(encoding="utf-8"))
    for line in (FIX / "audit_example.jsonl").read_text(encoding="utf-8").splitlines():
        AuditRecord.model_validate_json(line)


def test_abstain_requires_human_review() -> None:
    item = json.loads((FIX / "work_items_A.jsonl").read_text(encoding="utf-8").splitlines()[0])
    item["prediction"]["abstain"] = True
    item["prediction"]["abstain_reason"] = "test"
    with pytest.raises(ValidationError):
        WorkItem.model_validate(item)  # recommended_action nu e human_review


def test_source_kind_mismatch_rejected() -> None:
    item = json.loads((FIX / "work_items_A.jsonl").read_text(encoding="utf-8").splitlines()[0])
    item["kind"] = "voltage_mitigation"
    with pytest.raises(ValidationError):
        WorkItem.model_validate(item)
