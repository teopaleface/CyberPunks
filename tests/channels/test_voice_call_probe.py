"""The provider evaluator accepted incomplete replies in real API QA. Require execution evidence."""

import json
import runpy
from pathlib import Path

import pytest

probe = runpy.run_path(str(Path(__file__).resolve().parents[2] / "scripts/daybreak_whatsapp_call_probe.py"))
inspect_run, ProbeError = probe["inspect_run"], probe["ProbeError"]
QUESTION = "Care este următoarea mea oprire și de ce?"


@pytest.mark.parametrize("answer", [
    "Verific informațiile.",
    'daybreak_call_turn{"message":"Care este următoarea mea oprire și de ce?"} Următoarea oprire este în Sectorul 6.',
])
def test_provider_pass_does_not_replace_real_tool_execution(answer):
    with pytest.raises(ProbeError, match="actual tool"):
        inspect_run({"status": "passed", "agent_responses": [
            {"role": "user", "message": QUESTION}, {"role": "agent", "message": answer},
        ]}, QUESTION)


@pytest.mark.parametrize("executed", [False, True])
def test_probe_distinguishes_testing_placeholder_from_real_reply(executed):
    turns = [
        {"role": "user", "message": QUESTION},
        {"role": "agent", "tool_calls": [{
            "request_id": "synthetic-call", "tool_name": "daybreak_call_turn",
            "tool_has_been_called": executed, "params_as_json": json.dumps({"message": QUESTION}),
        }]},
        {"role": "agent", "tool_results": [{
            "request_id": "synthetic-call", "tool_has_been_called": executed, "is_error": False,
            "result_value": json.dumps({"reply": "Oprirea este în Sectorul 6."}) if executed else '{"reason":"Skipping tool call in test mode"}',
        }]},
        {"role": "agent", "message": "Oprirea este în Sectorul șase."},
    ]
    if executed:
        assert inspect_run({"agent_responses": turns}, QUESTION)["verified_reply"] == "Oprirea este în Sectorul 6."
    else:
        with pytest.raises(ProbeError, match="HTTP tool"):
            inspect_run({"agent_responses": turns}, QUESTION)
