"""Testele folosesc o copie completă a intrărilor modelului, niciodată mostra redusă."""

import os
import shutil
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from cyberpunks.common.paths import ROOT
from cyberpunks.operations.models import Actor
from cyberpunks.operations.router import router
from cyberpunks.operations.service import OperationsService, get_service
from cyberpunks.planner.agent import run


@pytest.fixture(scope="session")
def full_run(tmp_path_factory):
    root = tmp_path_factory.mktemp("operations-full-data")
    original = Path(os.environ.get("DAYBREAK_OPERATIONS_TEST_DATA", ROOT / "outputs")) / "plans/demo-vara"
    assert (original / "inputs").is_dir(), "Tests require the complete local model run, not sample fixtures."
    inputs = root / "work_items/demo-vara"
    inputs.mkdir(parents=True)
    for p in (original / "inputs").glob("*.jsonl"):
        shutil.copy2(p, inputs / p.name)
    # Real planner computation on every source/row, reusing predictions with their actual provenance.
    result = run("demo-vara", mode="existing", out_root=root, solver="greedy")
    assert result.plan.summary.items_valid >= 600
    return root


@pytest.fixture
def env(tmp_path, full_run, monkeypatch):
    root = tmp_path / "data"
    shutil.copytree(full_run, root)
    s = OperationsService(root, tmp_path / "registry.sqlite3")
    b = s.demo_bindings()
    actor = lambda uid, role, **kw: Actor(user_id=uid, role=role, organization_id="daybreak-demo", **kw)
    customer = actor("customer-1", "customer", connection_ids=b["connection_ids"])
    technician = actor("tech-1", "technician", crew_id=b["crew_id"])
    dispatcher = actor("dispatcher-1", "dispatcher", permissions=b["permissions"])
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_service] = lambda: s
    monkeypatch.setenv("DAYBREAK_INTERNAL_TOKEN", "test-internal-token-only")
    client = TestClient(app)

    def headers(a=customer, **kw):
        return {"Authorization": "Bearer test-internal-token-only", "X-Daybreak-Actor": a.model_dump_json(), **kw}

    return {
        "service": s,
        "client": client,
        "root": root,
        "binding": b["connections"][0],
        "customer": customer,
        "technician": technician,
        "dispatcher": dispatcher,
        "headers": headers,
    }


def propose(env, action, data, actor=None):
    actor = actor or env["customer"]
    r = env["client"].post(
        "/api/operations/proposals", headers=env["headers"](actor), json={"action": action, "data": data}
    )
    assert r.status_code == 200, r.text
    return r.json()


def confirm(env, proposal, actor=None):
    actor = actor or env["customer"]
    r = env["client"].post(
        "/api/operations/proposals/" + proposal["proposal_id"] + "/confirm", headers=env["headers"](actor)
    )
    assert r.status_code == 200, r.text
    return r.json()


def create_case(env, **kw):
    return confirm(
        env,
        propose(
            env,
            "create_case",
            {
                "connection_id": env["binding"]["connection_id"],
                "symptom": "Inverter stops at noon",
                "symptom_type": "meter",
                **kw,
            },
        ),
    )["result"]["case"]
