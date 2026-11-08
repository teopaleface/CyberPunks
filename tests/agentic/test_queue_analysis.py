from copy import deepcopy

import pytest

from cyberpunks.agentic.evidence import validate_analysis
from cyberpunks.agentic.queue_analysis import analyze_queue


def snapshot():
    return {
        "scenario": "demo",
        "plan": {"version": "v1", "plan_date": "2025-07-08"},
        "work_items": [
            {
                "work_item_id": str(i),
                "decision": {"decision": "human_review", "rule_id": "R-ABSTAIN"},
                "assessment": {"status": "needs_data"},
            }
            for i in range(31)
        ],
    }


def test_full_queue_and_abstention():
    context = snapshot()
    original = deepcopy(context)
    result = analyze_queue(context)
    assert result["total"] == 31
    assert result["analyzed_ids"] == [str(i) for i in range(31)]
    assert all(r["recommendation"] == "abstain" for r in result["items"])
    validate_analysis(context, result)
    assert context == original


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "version", "claim", "total"])
def test_reject_unsupported(mutation):
    context = snapshot()
    result = analyze_queue(context)
    if mutation == "missing":
        result["items"].pop()
    if mutation == "duplicate":
        result["items"].append(result["items"][0])
    if mutation == "version":
        context["plan"]["version"] = "v2"
    if mutation == "claim":
        result["items"][9]["assessment"]["score"] = 0.99
    if mutation == "total":
        result["total"] = 25
    with pytest.raises(ValueError):
        validate_analysis(context, result)
