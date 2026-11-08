"""Ziua plecării (planner/dispatch.py): urgent azi, restul în tura de zonă de vineri, fără să treacă termenul legal."""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from cyberpunks.common.contracts import WorkItem
from cyberpunks.planner import agent
from cyberpunks.planner.decide import Context, decide, is_free_day
from cyberpunks.planner.dispatch import add_working_days, sub_working_days, timing, tour_day
from cyberpunks.planner.ingest import Item
from cyberpunks.planner.settings import TZ, Settings

from .conftest import DATE, SCENARIO, fixture_items, variant, write_items

pytestmark = pytest.mark.weekly_batching

MONDAY = date(2026, 11, 9)
FRIDAY = date(2026, 11, 13)


def _settings(**dispatch: Any) -> Settings:
    s = Settings.load()
    s.planner.setdefault("dispatch", {}).update({"weekly_batching": True, **dispatch})
    return s


def _meter(asset: str, plan: date, registered: date | None = None, lat: float = 44.4512, lon: float = 26.1287, **changes: Any) -> Item:
    base = fixture_items("A")[1]  # contor defect
    # Un contor obișnuit: ~720 lei valoare așteptată, ~8 lei pierdere pe zi de așteptare (sub pragul de așteptare scumpă).
    changes = {"prediction.confidence": "high", "prediction.score": 0.9, "impact.value_if_true_lei": 800.0, **changes}
    raw = variant(base, asset, **changes)
    raw["target_date"] = plan.isoformat()
    raw["work_item_id"] = f"A-{plan:%Y%m%d}-{asset}"
    raw["location"].update(lat=lat, lon=lon)
    reg = registered or plan - timedelta(days=1)
    raw["created_at"] = datetime.combine(reg, datetime.min.time(), tzinfo=TZ).replace(hour=9).isoformat()
    text = json.dumps(raw, sort_keys=True)
    return Item(WorkItem.model_validate(raw), hashlib.sha256(text.encode()).hexdigest(), 1, "model")


def _decide(items: list[Item], plan: date, settings: Settings | None = None) -> tuple[Context, dict[str, Any]]:
    s = settings or _settings()
    as_of = datetime.combine(plan - timedelta(days=1), datetime.min.time(), tzinfo=TZ).replace(hour=18)
    ctx = Context.build(s, plan, as_of=as_of)
    return ctx, {p.id: p for p in decide(ctx, items)}


# ------------------------------------------------------------------ calendarul


def test_calendar_helpers() -> None:
    assert tour_day(MONDAY, [4]) == FRIDAY
    assert tour_day(FRIDAY, [4]) == FRIDAY
    assert tour_day(date(2026, 11, 14), [4]) == date(2026, 11, 20)  # sâmbătă: vinerea următoare
    assert tour_day(date(2026, 12, 21), [4]) == date(2026, 12, 24)  # 25 dec. e sărbătoare: tura e joi
    assert add_working_days(FRIDAY, 1) == date(2026, 11, 16)
    assert add_working_days(date(2026, 11, 27), 1) == date(2026, 12, 2)  # 30 nov. și 1 dec. sunt sărbători
    assert sub_working_days(date(2026, 11, 16), 1) == FRIDAY
    assert not is_free_day(sub_working_days(date(2026, 12, 2), 1))


# ------------------------------------------------------------------ regulile


def test_non_urgent_meter_waits_for_the_friday_tour() -> None:
    _, props = _decide([_meter("MTR-D0001", MONDAY)], MONDAY)
    p = props["A-20261109-MTR-D0001"]
    assert p.decision.value == "deferred" and p.rule_id == "R-WEEKLY-BATCH" and not p.route
    assert "vineri 13.11.2026" in p.reason_ro and "termenul legal" in p.reason_ro
    assert p.threshold["dispatch_wait_days"] == 4.0 and p.threshold["waiting_cost_lei"] > 0
    assert p.threshold["dispatch_limit_working_days"] == 10.0 and p.threshold["dispatch_legal_deadline"] == 1.0


def test_on_tour_day_the_meter_goes_out() -> None:
    _, props = _decide([_meter("MTR-D0002", FRIDAY)], FRIDAY)
    p = props["A-20261113-MTR-D0002"]
    assert p.route and p.rule_id == "R-A-VISIT" and p.threshold["dispatch_weekly_tour"] == 1.0
    assert not p.mandatory


def test_left_over_from_last_friday_does_not_wait_another_week() -> None:
    # Semnalat miercuri 4 nov.: tura lui era vineri 6 nov.; dacă n-a încăput, luni 9 nov. pleacă.
    _, props = _decide([_meter("MTR-D0006", MONDAY, registered=date(2026, 11, 4))], MONDAY)
    p = props["A-20261109-MTR-D0006"]
    assert p.route and p.rule_id == "R-A-VISIT" and "Nu a încăput în tura de zonă din vineri 06.11.2026" in p.reason_ro


def test_costly_wait_goes_now() -> None:
    # ~2.700 lei valoare așteptată: ~30 lei pe zi, ~120 lei până vineri, peste cât economisește tura pe o vizită
    _, props = _decide([_meter("MTR-D0007", MONDAY, **{"impact.value_if_true_lei": 3000.0})], MONDAY)
    p = props["A-20261109-MTR-D0007"]
    assert p.route and p.threshold["dispatch_wait_costly"] == 1.0 and "mai mult decât economisește" in p.reason_ro


def test_legal_deadline_forces_the_visit_today() -> None:
    # Sesizare luni 2 nov.: termenul e luni 16 nov. (10 zile lucrătoare), ultima zi sigură e vineri 13 nov.
    # Cu tura de zonă lunea, lucrarea ar aștepta până pe 16 (ziua termenului): pleacă vineri, obligatoriu.
    reg = date(2026, 11, 2)
    s = _settings(tour_weekdays=[0])  # tura de zonă lunea: ar trece de termen
    _, props = _decide([_meter("MTR-D0003", FRIDAY, registered=reg)], FRIDAY, s)
    p = props["A-20261113-MTR-D0003"]
    assert p.route and p.mandatory and p.rule_id == "R-LEGAL-DEADLINE"
    assert "termenul legal e luni 16.11.2026" in p.reason_ro


def test_large_customer_has_the_shorter_deadline() -> None:
    item = _meter("MTR-D0004", MONDAY, registered=MONDAY - timedelta(days=3))
    item.wi.extra["approved_power_kw"] = 150
    ctx, _ = _decide([], MONDAY)
    tm = timing(ctx, item.wi)
    assert tm.limit_days == 5 and tm.deadline == date(2026, 11, 13) and tm.last_safe == date(2026, 11, 12)
    assert tm.due == date(2026, 11, 12)  # înainte de vineri, din cauza termenului


def test_safety_case_is_never_postponed() -> None:
    item = _meter("MTR-D0005", MONDAY, **{"prediction.label": "tamper", "prediction.score": 0.97, "impact.safety_flag": True})
    _, props = _decide([item], MONDAY)
    p = props["A-20261109-MTR-D0005"]
    assert p.route and p.mandatory and p.rule_id == "R-SAFETY"


def test_a_full_zone_goes_before_friday() -> None:
    # 8 contoare la câteva sute de metri: 8 × (40 + 15) min = 7,3 h, peste 75% dintr-o tură de 7 h
    items = [_meter(f"MTR-D01{i:02d}", MONDAY, lat=44.4512 + 0.001 * i, lon=26.1287) for i in range(8)]
    _, props = _decide(items, MONDAY)
    assert {p.rule_id for p in props.values()} == {"R-A-VISIT"}
    assert all(p.route and p.threshold["dispatch_zone_full"] == 1.0 for p in props.values())


def test_a_meter_next_to_an_urgent_job_rides_along() -> None:
    urgent = _meter("MTR-D0201", MONDAY, **{"prediction.label": "tamper", "prediction.score": 0.97, "impact.safety_flag": True})
    near = _meter("MTR-D0202", MONDAY, lat=44.4532)  # ~0,3 km
    far = _meter("MTR-D0203", MONDAY, lat=44.60, lon=26.30)
    _, props = _decide([urgent, near, far], MONDAY)
    assert props[near.id].route and props[near.id].threshold["dispatch_on_the_way"] == 1.0 and not props[near.id].mandatory
    assert props[far.id].rule_id == "R-WEEKLY-BATCH"


@pytest.mark.parametrize("days_ago", range(15))
def test_waiting_never_passes_the_deadline(days_ago: int) -> None:
    for plan in (MONDAY + timedelta(days=k) for k in range(7)):
        if is_free_day(plan):
            continue
        item = _meter(f"MTR-D03{days_ago:02d}", plan, registered=plan - timedelta(days=days_ago))
        ctx, props = _decide([item], plan)
        p = props[item.id]
        tm = timing(ctx, item.wi)
        if p.rule_id == "R-WEEKLY-BATCH":
            assert plan < tm.due <= tm.last_safe < tm.deadline
        else:
            assert p.route  # azi: tura, termenul sau zona
            assert plan <= tm.deadline


def test_switch_off_restores_next_day_routing() -> None:
    _, props = _decide([_meter("MTR-D0004", MONDAY)], MONDAY, _settings(weekly_batching=False))
    assert props["A-20261109-MTR-D0004"].route


def test_end_to_end_plan_records_the_dispatch_summary(out_root: Path) -> None:
    a = fixture_items("A")
    rows = [variant(a[1], f"MTR-73{i:04d}", **{"prediction.confidence": "high", "prediction.score": 0.9,
                                               "impact.value_if_true_lei": 800.0}) for i in range(2)]
    write_items(out_root, "A", rows)
    res = agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root)  # luni
    decisions = {d.work_item_id: d for d in res.plan.decisions}
    assert all(decisions[r["work_item_id"]].rule_id == "R-WEEKLY-BATCH" for r in rows)
    assert res.meta["dispatch"]["enabled"] and res.meta["dispatch"]["deferred"] == 2
