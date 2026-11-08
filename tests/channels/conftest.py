"""API tests on a fresh full-data planner run, with an explicitly simulated conversation provider."""

import os
import shutil
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from cyberpunks.channels.conversation import ConversationService
from cyberpunks.channels.limits import Limits
from cyberpunks.channels.models import Intention, IntentionData
from cyberpunks.channels.router import get_conversation, router
from cyberpunks.common.paths import ROOT
from cyberpunks.operations.models import Actor
from cyberpunks.operations.service import OperationsService
from cyberpunks.planner.agent import run


class SimulatedProvider:
    def __init__(self):
        self.output = intention()
        self.prompts = []
        self.error = None

    async def turn(self, prompt):
        self.prompts.append(prompt)
        if self.error:
            raise self.error
        return self.output, {"provider": "simulated-test-provider", "model": "test-only", "tools_enabled": False}


def intention(kind="clarify", reply="Which connection do you mean?", action=None, evidence=None, **data):
    empty = dict.fromkeys(IntentionData.model_fields)
    empty.update(data)
    return Intention(kind=kind, reply=reply, language="en", action=action, data=empty, evidence=evidence or [])


@pytest.fixture(scope="session")
def full_run(tmp_path_factory):
    root = tmp_path_factory.mktemp("channels-complete-data")
    original = Path(os.getenv("DAYBREAK_OPERATIONS_TEST_DATA", str(ROOT / "outputs"))) / "plans/demo-vara/inputs"
    assert original.is_dir(), "A complete current local run is required, not a sample fixture."
    target = root / "work_items/demo-vara"
    target.mkdir(parents=True)
    for path in original.glob("*.jsonl"):
        shutil.copy2(path, target / path.name)
    result = run("demo-vara", mode="existing", out_root=root, solver="greedy")
    assert result.plan.summary.items_valid >= 600
    return root


@pytest.fixture
def env(tmp_path, full_run, monkeypatch):
    root = tmp_path / "full-data"
    shutil.copytree(full_run, root)
    operations = OperationsService(root, tmp_path / "operations.sqlite3")
    binding = operations.demo_bindings()
    base = {"organization_id": binding["organization_id"]}
    actors = {
        "customer": Actor(
            user_id="synthetic-customer", role="customer", connection_ids=binding["connection_ids"], **base
        ),
        "technician": Actor(user_id="synthetic-technician", role="technician", crew_id=binding["crew_id"], **base),
        "dispatcher": Actor(
            user_id="synthetic-dispatcher", role="dispatcher", permissions=binding["permissions"], **base
        ),
    }
    provider = SimulatedProvider()
    conversation = ConversationService(operations, provider)
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_conversation] = lambda: conversation
    import cyberpunks.channels.router as routes

    monkeypatch.setattr(routes, "limits", Limits(per_minute=100))
    monkeypatch.setenv("DAYBREAK_INTERNAL_TOKEN", "synthetic-internal-test-token")
    monkeypatch.setenv("DAYBREAK_CHANNELS_RUNTIME", str(tmp_path))
    client = TestClient(app)

    def headers(role="customer", **changes):
        return {
            "Authorization": "Bearer synthetic-internal-test-token",
            "X-Daybreak-Actor": actors[role].model_dump_json(),
            **changes,
        }

    return {
        "operations": operations,
        "actors": actors,
        "provider": provider,
        "client": client,
        "headers": headers,
        "conversation": conversation,
        "binding": binding,
        "tmp": tmp_path,
    }


def call(env, account_role="customer", **body):
    return env["client"].post(
        "/api/conversation/chat", headers=env["headers"](account_role), json={"message": "Help", **body}
    )
