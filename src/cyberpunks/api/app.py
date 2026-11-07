"""API-ul agentului pentru consola dispecerului (http://127.0.0.1:8710/api).

    make api        # uv run uvicorn cyberpunks.api.app:app --host 127.0.0.1 --port 8710

Contractul: docs/CONTRACTS.md. Documentația interactivă: http://127.0.0.1:8710/docs
Datele vin din ultima rulare a agentului, din instantaneul outputs/demo/ sau din contracts/fixtures/
(vezi cyberpunks.api.store). Răspunsul la /health spune ce mod e folosit.
"""

from __future__ import annotations

import re
import threading
from typing import Any, Literal

from fastapi import APIRouter, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field

from cyberpunks import __version__
from cyberpunks.api.store import Store
from cyberpunks.common.contracts import CONTRACT_VERSION
from cyberpunks.planner import planner_version
from cyberpunks.planner.settings import Settings

DEFAULT_SCENARIO = "demo-vara"
_SCENARIO_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_ITEM_RE = re.compile(r"^[ABC]-\d{8}-[A-Za-z0-9_.-]+$")
_CREW_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")

store = Store()
_run_lock = threading.Lock()  # o singură rulare a agentului odată

app = FastAPI(
    title="Tura de mâine: API-ul agentului",
    version=__version__,
    description="Planul echipelor de teren Rețele Electrice (date sintetice și publice). SmartHack XI 2026, tema PPC.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3710", "http://127.0.0.1:3710"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
api = APIRouter(prefix="/api")


# ------------------------------------------------------------------ validarea parametrilor


def _scenario(value: str) -> str:
    if not _SCENARIO_RE.match(value):
        raise HTTPException(422, f"scenariu invalid: {value!r}")
    return value


def _item_id(value: str) -> str:
    if not _ITEM_RE.match(value):
        raise HTTPException(422, f"ID de lucrare invalid: {value!r} (formatul e <A|B|C>-<YYYYMMDD>-<activ>)")
    return value


def _plan_or_404(scenario: str) -> dict[str, Any]:
    plan = store.view(scenario).plan()
    if plan is None:
        raise HTTPException(404, f"nu există plan pentru scenariul {scenario!r}")
    return plan


# ------------------------------------------------------------------ cereri


class RunRequest(BaseModel):
    scenario: str = DEFAULT_SCENARIO
    date: str | None = Field(default=None, description="YYYY-MM-DD; implicit data din config/scenarios.yaml")


class ReviewRequest(BaseModel):
    decision: Literal["approve", "reject", "defer"]
    note: str | None = Field(default=None, max_length=2000)
    reviewer: str = Field(default="dispecer", min_length=1, max_length=100)


# ------------------------------------------------------------------ rute


@api.get("/health")
def health(scenario: str = DEFAULT_SCENARIO) -> dict[str, Any]:
    view = store.view(_scenario(scenario))
    plan = view.plan() or {}
    return {
        "status": "ok",
        "version": __version__,
        "planner_version": planner_version(),
        "contract_version": CONTRACT_VERSION,
        "scenario": scenario,
        "mode": view.mode,
        "sources_status": plan.get("sources_status", {}),
    }


@api.get("/scenarios")
def scenarios() -> list[dict[str, Any]]:
    settings = Settings.load()
    out = []
    for sid, sc in settings.scenarios.items():
        d = sc.resolve_date()
        view = store.view(sid)
        out.append(
            {
                "scenario_id": sid,
                "label_ro": sc.label_ro,
                "date": d.isoformat() if d else None,
                "weather": sc.weather,
                "mode": view.mode,
                "has_plan": view.mode != "fixtures",
            }
        )
    return out


@api.post("/run")
def run(req: RunRequest) -> dict[str, Any]:
    scenario = _scenario(req.scenario)
    try:
        from cyberpunks.planner import agent
    except ImportError as exc:  # agentul nu e încă gata (M1)
        raise HTTPException(503, f"agentul nu e încă disponibil: {exc}") from exc
    if not _run_lock.acquire(blocking=False):
        raise HTTPException(409, "agentul rulează deja; încearcă din nou peste câteva secunde")
    try:
        result = agent.run(scenario=scenario, date=req.date)
    finally:
        _run_lock.release()
    return {"plan_id": result.plan.plan_id, "timings": result.timings, "summary": result.plan.summary.model_dump()}


@api.get("/plan")
def plan(scenario: str = DEFAULT_SCENARIO) -> dict[str, Any]:
    return _plan_or_404(_scenario(scenario))


@api.get("/work-items")
def work_items(scenario: str = DEFAULT_SCENARIO, source: Literal["A", "B", "C"] | None = None) -> list[dict[str, Any]]:
    items = store.view(_scenario(scenario)).work_items()
    return [w for w in items if source is None or w.get("source") == source]


@api.get("/work-items/{work_item_id}")
def work_item(work_item_id: str, scenario: str = DEFAULT_SCENARIO) -> dict[str, Any]:
    _item_id(work_item_id)
    view = store.view(_scenario(scenario))
    item = next((w for w in view.work_items() if w.get("work_item_id") == work_item_id), None)
    if item is None:
        raise HTTPException(404, f"lucrarea {work_item_id} nu există în scenariul {scenario!r}")
    plan = view.plan() or {}
    decision = next((d for d in plan.get("decisions", []) if d.get("work_item_id") == work_item_id), None)
    return {**item, "decision": decision}


@api.get("/series/{work_item_id}")
def series(work_item_id: str, scenario: str = DEFAULT_SCENARIO) -> dict[str, Any]:
    _item_id(work_item_id)
    found = store.view(_scenario(scenario)).series(work_item_id)
    if found is None:
        raise HTTPException(404, f"nu există serie pentru {work_item_id}")
    return found


@api.get("/audit")
def audit(scenario: str = DEFAULT_SCENARIO, work_item_id: str | None = None) -> list[dict[str, Any]]:
    records = store.view(_scenario(scenario)).audit()
    if work_item_id:
        records = [r for r in records if r.get("work_item_id") == work_item_id]
    return records


@api.post("/review/{work_item_id}")
def review(work_item_id: str, req: ReviewRequest, scenario: str = Query(DEFAULT_SCENARIO)) -> dict[str, Any]:
    _item_id(work_item_id)
    scenario = _scenario(scenario)
    try:
        from cyberpunks.planner import review as review_mod
    except ImportError as exc:
        raise HTTPException(503, f"revizuirea nu e încă disponibilă: {exc}") from exc
    if not _run_lock.acquire(timeout=30):
        raise HTTPException(409, "agentul rulează; încearcă din nou")
    try:
        record = review_mod.apply_review(
            scenario=scenario, work_item_id=work_item_id, decision=req.decision, note=req.note, reviewer=req.reviewer
        )
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    finally:
        _run_lock.release()
    return record.model_dump(mode="json")


@api.get("/metrics")
def metrics() -> dict[str, Any]:
    return store.metrics()


@api.get("/work-orders/{crew_id}.pdf")
def work_order(crew_id: str, scenario: str = DEFAULT_SCENARIO) -> FileResponse:
    if not _CREW_RE.match(crew_id):
        raise HTTPException(422, f"echipă invalidă: {crew_id!r}")
    path = store.view(_scenario(scenario)).work_order_pdf(crew_id)
    if path is None:
        raise HTTPException(404, f"nu există ordin de lucru pentru echipa {crew_id}")
    return FileResponse(path, media_type="application/pdf", filename=f"ordin-de-lucru-{crew_id}.pdf")


# ---- rute în plus față de contract (comode pentru interfață) ----


@api.get("/quarantine")
def quarantine(scenario: str = DEFAULT_SCENARIO) -> list[dict[str, Any]]:
    """Intrările respinse la validare (carantina), cu motivele."""
    return store.view(_scenario(scenario)).quarantine()


@api.get("/alerts")
def alerts(scenario: str = DEFAULT_SCENARIO) -> list[dict[str, Any]]:
    return _plan_or_404(_scenario(scenario)).get("alerts", [])


@api.get("/notifications")
def notifications(scenario: str = DEFAULT_SCENARIO) -> list[dict[str, Any]]:
    return _plan_or_404(_scenario(scenario)).get("notifications", [])


@api.get("/report", response_class=PlainTextResponse)
def report(scenario: str = DEFAULT_SCENARIO) -> str:
    text = store.view(_scenario(scenario)).report_md()
    if text is None:
        raise HTTPException(404, "raportul zilei nu există încă pentru acest scenariu")
    return text


app.include_router(api)
