"""The field sheet keeps every stop and verified values in human-readable form."""

import subprocess

from cyberpunks.agentic.pdf_renderer import render_pdf
from cyberpunks.agentic.pdf_report import pdf_pages, reason_for_visit, report_filename


def test_field_sheet_has_every_stop_readable_times_and_no_internal_filename(tmp_path):
    data = {
        "kind": "technician",
        "historical_date": "2025-07-08",
        "generated_at": "2026-11-08T10:00:00+02:00",
        "state": "approved",
        "synthetic": True,
        "rows": [
            {
                "title": f"MTR-{i:06d}",
                "work_item_id": f"INTERNAL-{i}",
                "eta": f"2025-07-08T08:{i:02d}:00+03:00",
                "duration_min": 5,
                "travel_km": 1.45,
                "reason": "57% din ultimele 4 săptămâni fără date; cel mai lung gol: 9 zile fără date. Scor 98%, încredere mare.",
            }
            for i in range(6)
        ],
    }
    assert report_filename(data) == "Daybreak-Traseu-8-iulie-2025.pdf"
    html = pdf_pages(data)
    assert html[0].count("OPRIREA ") == 6
    assert "1,45 km" in html[0] and "2025-07-08T08" not in html[0] and "INTERNAL-" not in html[0]
    result = render_pdf(html)
    assert result["page_count"] == 1
    path = tmp_path / "sheet.pdf"
    path.write_bytes(result["pdf"])
    text = subprocess.check_output(["pdftotext", str(path), "-"]).decode()
    assert all(f"MTR-{i:06d}" in text for i in range(6))
    assert "Pagina 1 din 1" in text and "30 min" in text
    data["rows"][0]["title"] = "<script>alert(1)</script>"
    assert "&lt;script&gt;" in pdf_pages(data)[0]


def test_weather_safety_reason_is_not_rewritten_as_a_meter_balance_problem():
    reason = "Risc pentru siguranța oamenilor: vânt puternic în zona intervenției."
    assert reason_for_visit(reason) == reason
