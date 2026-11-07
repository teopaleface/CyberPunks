"""Verdictele după vizită devin etichete."""

from __future__ import annotations

import json

import pandas as pd

from cyberpunks.a_bilant import feedback


def test_collect_and_relabel(tmp_path, monkeypatch):
    monkeypatch.setattr(feedback, "plan_dir", lambda s: tmp_path)
    recs = [
        {"actor": "human", "action": "review:approve", "work_item_id": "A-20250708-PT-1132", "note": "Verdict: furt_inainte_contor, branșament direct", "prediction_id": "p1", "ts": "2025-07-08T10:00:00+03:00"},
        {"actor": "human", "action": "review:reject", "work_item_id": "A-20250708-PT-1009", "note": "nimic găsit", "prediction_id": "p2", "ts": "2025-07-08T11:00:00+03:00"},
        {"actor": "agent", "action": "decide", "work_item_id": "A-20250708-PT-1004", "note": "verdict:normal"},
        {"actor": "human", "action": "review:approve", "work_item_id": "A-20250708-MTR-000001", "note": "verdict:normal"},
    ]
    (tmp_path / "audit.jsonl").write_text("".join(json.dumps(r) + "\n" for r in recs))
    v = feedback.collect("demo-vara")
    assert dict(zip(v["post_id"], v["verdict"], strict=True)) == {"PT-1132": "furt_inainte_contor", "PT-1009": "normal"}
    win = pd.DataFrame({"post_id": ["PT-1132", "PT-1009", "PT-1004"], "date": pd.to_datetime(["2025-07-08"] * 3), "true_class": ["contor_client", "contor_client", "normal"]})
    w = feedback.windows_with_verdicts(win, v)
    assert w["true_class"].tolist() == ["furt_inainte_contor", "normal", "normal"]
    assert w["weight"].tolist() == [feedback.VERDICT_WEIGHT, feedback.VERDICT_WEIGHT, 1.0]
