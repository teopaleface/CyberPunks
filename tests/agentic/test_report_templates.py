from cyberpunks.agentic.report_data import build_report_data
from cyberpunks.agentic.report_templates import render_report


def test_scope_escape_and_pagination():
    context = {
        "actor": {"role": "customer"},
        "scenario": "demo-vara",
        "cases": [{"case_id": "<script>alert(1)</script>", "status": "open", "secret": "PRIVATE"}] * 7,
    }
    data = build_report_data(context)
    pages = render_report(data)
    assert len(pages) == 3
    assert all("PRIVATE" not in p and "<script>" not in p for p in pages)
    assert "&lt;script&gt;" in pages[0]
    assert "2025-07-08" in data["text"]
