"""Ordinele de lucru PDF: câte unul pe echipă, curățenie la rescriere."""

from __future__ import annotations

from pathlib import Path

from cyberpunks.common.paths import CONTRACTS
from cyberpunks.planner import agent
from cyberpunks.planner.ingest import Item, load_source
from cyberpunks.planner.settings import Settings
from cyberpunks.planner.workorders import write_work_orders

FIX = CONTRACTS / "fixtures"


def test_work_orders_pdf(tmp_path: Path) -> None:
    out_root = tmp_path / "out"
    res = agent.run("demo-vara", mode="fixtures", out_root=out_root)
    plan = res.plan
    wo = res.plan_dir / "work_orders"
    assert plan.routes
    for r in plan.routes:
        pdf = wo / f"{r.crew_id}.pdf"
        assert pdf.exists()
        data = pdf.read_bytes()
        assert data.startswith(b"%PDF") and len(data) > 5_000

    items: list[Item] = []
    for s in "ABC":
        items += load_source(s, FIX / f"work_items_{s}.jsonl", "fixture", plan.plan_date, set()).items
    assert len(items) >= 4
    stale = wo / "E-OLD.pdf"
    stale.write_bytes(b"%PDF-old")
    paths = write_work_orders(plan, items, res.plan_dir, Settings.load())
    assert {p.name for p in paths} == {f"{r.crew_id}.pdf" for r in plan.routes}
    assert not stale.exists()
