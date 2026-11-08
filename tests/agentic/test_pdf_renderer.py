"""Real Chromium PDF rendering of the fixed report templates. Data is synthetic."""

import re
import shutil
import subprocess
from datetime import UTC, datetime
from hashlib import sha256

import pytest

from cyberpunks.agentic.pdf_renderer import describe_pdf, render_pdf
from cyberpunks.agentic.report_templates import render_report


def synthetic(rows=7):
    return {
        "kind": "dispatcher",
        "title": "Lista dispecerului",
        "scenario": "demo-vara",
        "plan_version": "synthetic-v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "historical_date": "2025-07-08",
        "synthetic": True,
        "rows": [
            {
                "title": f"Locație sintetică {i}: ăîșțâ <b>nu e markup</b>",
                "work_item_id": f"WI-{i:04d}",
                "recommendation": "human_review",
                "reason": "Motiv sintetic",
            }
            for i in range(rows)
        ],
        "state": "proposed",
        "language": "ro",
    }


def test_rejects_unsafe_or_oversized_input():
    assert pytest.raises(ValueError, render_pdf, [])
    for html in ["<script>alert(1)</script>", '<img src="file:///etc/passwd">', '<body onclick="x">']:
        with pytest.raises(ValueError):
            render_pdf([html])
    with pytest.raises(ValueError):
        render_pdf(["x" * 128001])
    with pytest.raises(ValueError):
        render_pdf(["<p>x</p>"] * 251)


def test_describe_pdf_checks_the_envelope():
    for bad in (b"", b"\x89PNG\r\n\x1a\n", b"%PDF-1.7\n%%EOF", b"%PDF-1.7 truncated"):
        with pytest.raises(ValueError):
            describe_pdf(bad)
    with pytest.raises(ValueError):
        describe_pdf(b"%PDF-1.7\n" + b"x" * 8_000_001 + b"\n%%EOF")


def test_real_pdf_has_one_a4_page_per_source_page_and_exact_identity(tmp_path):
    pages = render_report(synthetic())
    assert len(pages) == 3
    result = render_pdf(pages)
    pdf = result["pdf"]
    assert pdf.startswith(b"%PDF-") and result["bytes"] == len(pdf) < 8_000_000
    assert result["sha256"] == sha256(pdf).hexdigest()
    assert result["source_pages"] == 3 and result["page_count"] == 3
    target = tmp_path / "report.pdf"
    target.write_bytes(pdf)
    if not shutil.which("pdftotext"):
        pytest.skip("poppler is not installed")
    info = subprocess.run(["pdfinfo", str(target)], capture_output=True, text=True, check=True).stdout
    assert "Pages:           3" in info and "A4" in info and "PPC Daybreak report" in info
    text = subprocess.run(["pdftotext", "-layout", str(target), "-"], capture_output=True, text=True, check=True).stdout
    assert "Lista dispecerului" in text and "ăîșțâ" in text
    assert "Pagina 1 din 3" in text and "Pagina 3 din 3" in text
    assert text.count("Confirmarea se face în aplicația autentificată.") == 3
    # Report data is escaped text, never interpreted as markup.
    assert "<b>nu e markup</b>" in text
    assert "Include date sintetice" in text


def test_real_role_reports(env):
    from cyberpunks.agentic.report_data import build_report_data

    for role in ("dispatcher", "technician", "customer"):
        context = env["service"].context(env[role])
        data = build_report_data(context)
        result = render_pdf(render_report(data))
        assert result["page_count"] >= 1 and result["sha256"] == sha256(result["pdf"]).hexdigest()


def _page_text(path, number):
    return subprocess.run(
        ["pdftotext", "-f", str(number), "-l", str(number), str(path), "-"], capture_output=True, text=True, check=True
    ).stdout


@pytest.mark.skipif(not shutil.which("pdftotext"), reason="poppler is not installed")
@pytest.mark.parametrize("reason_words", [20, 330])
def test_footer_counts_physical_pages_and_every_row_is_present(tmp_path, reason_words):
    """Six technician rows. Long reasons overflow a source page onto more physical pages."""
    rows = [
        {
            "work_item_id": f"SYN-REF-{i:03d}",
            "eta": f"2025-07-08T0{8 + i}:32:00+03:00",
            "duration_min": "5",
            "seq": str(i + 1),
            "travel_km": "0.69",
            "reason": f"Marcaj{i}x " + " ".join(f"cuvânt{i}n{n}" for n in range(reason_words)) + f" final{i}z",
            "status": "approved",
        }
        for i in range(6)
    ]
    data = {**synthetic(), "kind": "technician", "title": "Traseu aprobat", "rows": rows, "state": "approved"}
    sources = render_report(data)
    assert len(sources) == 2
    result = render_pdf(sources)
    target = tmp_path / "technician.pdf"
    target.write_bytes(result["pdf"])
    total = result["page_count"]
    info = subprocess.run(["pdfinfo", str(target)], capture_output=True, text=True, check=True).stdout
    assert f"Pages:           {total}" in info
    if reason_words == 20:
        assert total == 2, "three compact cards must fit one A4 page"
    else:
        assert total > len(sources), "the long variant must really overflow source pages"
    everything = ""
    for number in range(1, total + 1):
        text = _page_text(target, number)
        footers = re.findall(r"Pagina (\d+) din (\d+)\.", text)
        # Exactly one footer per physical page, with the physical number and total. The template's own
        # "Pagina N din 2" footer is hidden, so it can never contradict this one.
        assert footers == [(str(number), str(total))], (number, footers)
        assert text.count("Confirmarea se face în aplicația autentificată.") == 1
        everything += text + "\n"
    # The header opens each source page once; continuation pages carry cards only.
    assert everything.count("PPC · Daybreak") == len(sources)
    flat = " ".join(everything.split())
    for i, row in enumerate(rows):
        assert flat.count(row["work_item_id"]) == 1
        assert " ".join(row["reason"].split()) in flat, f"row {i} text is incomplete or reordered"
    assert flat.index("SYN-REF-000") < flat.index("SYN-REF-005")
