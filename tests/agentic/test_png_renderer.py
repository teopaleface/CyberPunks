from hashlib import sha256

import pytest

from cyberpunks.agentic.png_renderer import render_pages
from cyberpunks.agentic.report_templates import render_report


def test_limits_and_script():
    assert render_pages([]) == []
    for html in ["<script>alert(1)</script>", '<img src="file:///etc/passwd">', '<body onclick="x">']:
        with pytest.raises(ValueError):
            render_pages([html])
    with pytest.raises(ValueError):
        render_pages(["x" * 128001])


def test_real_reports(env):
    from pathlib import Path

    from cyberpunks.agentic.report_data import build_report_data

    for role in ("dispatcher", "technician", "customer"):
        context = env["service"].context(env[role])
        data = build_report_data(context)
        assert data["plan_version"] == context["plan"]["version"]
        if role != "customer":
            assert data["rows"]
        pages = render_pages(render_report(data)[:2])
        for p in pages:
            assert p["width"] == 360
            assert sha256(p["png"]).hexdigest() == p["sha256"]
            Path(f"/tmp/daybreak-job03-{role}-{p['page']}.png").write_bytes(p["png"])
