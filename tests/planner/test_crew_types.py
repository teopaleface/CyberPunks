"""Regula tipurilor de echipe (8 nov. 2026): echipe de înaltă și medie tensiune și echipe de joasă tensiune; fiecare ia doar
lucrările specializării ei."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any

import pytest

from cyberpunks.common.contracts import WorkItem
from cyberpunks.planner.agent import build_routing
from cyberpunks.planner.decide import Context, check_crews, decide
from cyberpunks.planner.ingest import Item
from cyberpunks.planner.settings import TZ, Settings, load_crews

from .conftest import DATE, fixture_items, variant

PLAN = datetime.fromisoformat(DATE).date()


def _item(raw: dict[str, Any]) -> Item:
    text = json.dumps(raw, sort_keys=True)
    return Item(WorkItem.model_validate(raw), hashlib.sha256(text.encode()).hexdigest(), 1, "model")


def _ctx(s: Settings | None = None) -> Context:
    s = s or Settings.load()
    return Context.build(s, PLAN, as_of=datetime.combine(PLAN - timedelta(days=1), datetime.min.time(), tzinfo=TZ).replace(hour=18))


def _allowed_types(ctx: Context, items: list[Item]) -> dict[str, set[str]]:
    pb = build_routing(ctx, decide(ctx, items))
    return {t.id: {pb.vehicles[v].crew.crew_type for v in t.allowed} for t in pb.tasks}


def test_every_crew_has_exactly_one_type() -> None:
    s = Settings.load()
    assert set(s.crew_types) == {"it_mt", "jt"}
    for c in s.crews:
        assert c.crew_type in s.crew_types
        assert c.skills == frozenset(s.crew_types[c.crew_type]["skills"])
        assert not {"lv_grid", "mv_grid"} <= c.skills  # nicio echipă nu face și JT, și MT
    assert {c.crew_type for c in s.crews} == {"it_mt", "jt"}
    assert s.crew_type_of("metering") == "jt" and s.crew_type_of("lv_grid") == "jt"
    assert s.crew_type_of("mv_grid") == "it_mt" and s.crew_type_of("hv_grid") == "it_mt"


@pytest.mark.parametrize(
    ("cfg", "match"),
    [
        ({"crew_types": {"jt": {"skills": ["lv_grid"]}}, "crews": [{"crew_id": "X", "depot_id": "D", "type": "jt", "skills": ["mv_grid"]}]}, "skills"),
        ({"crew_types": {"jt": {"skills": ["lv_grid"]}}, "crews": [{"crew_id": "X", "depot_id": "D", "type": "mixt"}]}, "tipul"),
        ({"crew_types": {"jt": {"skills": ["lv_grid"]}, "it_mt": {"skills": ["lv_grid", "mv_grid"]}}, "crews": []}, "un singur tip"),
    ],
)
def test_config_cannot_break_the_rule(cfg: dict[str, Any], match: str) -> None:
    with pytest.raises(ValueError, match=match):
        load_crews(cfg)


def test_meter_visit_goes_only_to_low_voltage_crews() -> None:
    raw = variant(fixture_items("A")[1], "MTR-CT0001", **{"prediction.confidence": "high", "prediction.score": 0.9})
    allowed = _allowed_types(_ctx(), [_item(raw)])
    assert allowed[raw["work_item_id"]] == {"jt"}


@pytest.mark.parametrize(("skill", "crew_type"), [("mv_grid", "it_mt"), ("lv_grid", "jt")])
def test_storm_goes_only_to_the_matching_crew_type(skill: str, crew_type: str) -> None:
    raw = variant(fixture_items("B")[0], f"STORM-{skill}", **{"effort.crew_skill": skill})
    ctx = _ctx()
    props = {p.id: p for p in decide(ctx, [_item(raw)])}
    p = props[raw["work_item_id"]]
    required = p.skills_required or frozenset({p.skill or p.wi.effort.crew_skill.value})
    eligible = {c.crew_type for c in ctx.settings.crews if required <= c.skills}
    assert eligible == {crew_type}


def test_job_without_a_crew_of_its_type_says_so() -> None:
    s = Settings.load()
    s.crews = [c for c in s.crews if c.crew_type == "jt"]  # nicio echipă de înaltă și medie tensiune
    raw = variant(fixture_items("B")[0], "STORM-NOMT", **{"effort.crew_skill": "mv_grid"})
    ctx = _ctx(s)
    p = next(p for p in decide(ctx, [_item(raw)]) if p.id == raw["work_item_id"])
    assert not p.route
    assert "Nicio echipă de înaltă și medie tensiune" in p.reason_ro, (p.rule_id, p.reason_ro)


def test_check_crews_names_the_crew_type() -> None:
    s = Settings.load()
    s.crews = [c for c in s.crews if c.crew_type == "jt"]
    raw = variant(fixture_items("A")[1], "MTR-CT0002", **{"prediction.confidence": "high", "prediction.score": 0.9,
                                                          "effort.crew_skill": "mv_grid"})
    ctx = _ctx(s)
    s.planner.setdefault("dispatch", {})["weekly_batching"] = False
    from cyberpunks.planner.decide import propose

    p = check_crews(ctx, propose(ctx, _item(raw)))
    assert not p.route and "Nicio echipă de înaltă și medie tensiune" in p.reason_ro
