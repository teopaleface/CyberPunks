"""Efecte reale în planificator, pregătite separat și reconciliate după întrerupere.

SQLite și fișierele nu împart o tranzacție. Manifestul durabil conține versiunea
anterioară și hash-ul fiecărui rezultat; publicarea repetată nu reaplică funcția.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path

from cyberpunks.api.store import DEMO, ScenarioView, read_json
from cyberpunks.operations.models import OperationError


def digest(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def dump(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8") as out:
        json.dump(value, out, ensure_ascii=False, sort_keys=True)
        out.flush()
        os.fsync(out.fileno())
    os.replace(temp, path)


class Planner:
    def __init__(self, outputs: Path, state: Path, demo: Path = DEMO):
        self.outputs, self.state, self.demo = outputs, state, demo

    def view(self, scenario: str) -> ScenarioView:
        if (self.outputs / "plans" / scenario / "plan.json").exists():
            return ScenarioView(scenario, "live", self.outputs)
        if (self.demo / "plans" / scenario / "plan.json").exists():
            return ScenarioView(scenario, "demo", self.demo)
        raise OperationError(503, "plan_unavailable", "No complete scenario plan is available.")

    def version(self, scenario: str) -> str:
        view = self.view(scenario)
        names = [
            "plan.json",
            "work_items.jsonl",
            "actions.json",
            "overrides.json",
            "approvals.json",
            "plan_approval.json",
            "labels.jsonl",
            "run.json",
        ]
        raw = [(n, digest(view.plan_dir / n)) for n in names]
        return hashlib.sha256(json.dumps(raw).encode()).hexdigest()

    def writable(self, scenario: str):
        view = self.view(scenario)
        meta = read_json(view.plan_dir / "run.json") or {}
        if (
            view.mode != "live"
            or self.outputs == self.demo.resolve()
            or meta.get("mode") not in ("auto", "existing", "replan")
        ):
            raise OperationError(409, "read_only_snapshot", "Generate a local planner run before changing its plan.")
        if not (view.plan_dir / "inputs").is_dir():
            raise OperationError(409, "missing_run_inputs", "The local run has no reproducible planner inputs.")

    def execute(self, command: dict, proposal: dict, actor_id: str) -> dict:
        """Cheia comenzii și manifestul fac retry-ul sigur inclusiv după publicare parțială."""
        cid, scenario = command["command_id"], proposal["scenario"]
        base = self.state / "effects" / cid
        manifest_path = base / "effect.json"
        manifest = read_json(manifest_path)
        if manifest is None:
            self.writable(scenario)
            if self.version(scenario) != proposal["plan_version"]:
                raise OperationError(409, "stale_plan", "The plan changed. Prepare a new proposal.")
            source = self.outputs / "plans" / scenario
            stage = base / "stage"
            target = stage / "plans" / scenario
            if stage.exists():
                shutil.rmtree(stage)  # only this command's incomplete private staging directory
            shutil.copytree(source, target)
            before = {str(p.relative_to(source)): digest(p) for p in source.rglob("*") if p.is_file()}
            d, action = proposal["data"], proposal["action"]
            note = (d.get("note") or "") + f" [daybreak-command:{cid}]"
            from cyberpunks.planner import feedback

            if action == "approve_plan":
                if d.get("crew_id"):
                    effect = feedback.approve_route(scenario, d["crew_id"], actor_id, note, out_root=stage)
                else:
                    record = feedback.approve_plan(scenario, d["plan_id"], actor_id, note, out_root=stage)
                    effect = {"audit": record.model_dump(mode="json")}
            elif action == "record_verdict":
                record, label = feedback.record_verdict(
                    scenario, d["work_item_id"], d["outcome"], actor_id, note, out_root=stage
                )
                effect = {"audit": record.model_dump(mode="json"), "label": label}
            else:
                from cyberpunks.planner.review import apply_review

                record = apply_review(scenario, d["work_item_id"], d["decision"], note, actor_id, out_root=stage)
                effect = {"audit": record.model_dump(mode="json")}
            changes = []
            for p in sorted(target.rglob("*")):
                if p.is_file():
                    name = str(p.relative_to(target))
                    after = digest(p)
                    if before.get(name) != after:
                        changes.append({"path": name, "before": before.get(name), "after": after})
            after_names = {str(p.relative_to(target)) for p in target.rglob("*") if p.is_file()}
            for name in sorted(before.keys() - after_names):
                changes.append({"path": name, "before": before[name], "after": None})
            manifest = {
                "command_id": cid,
                "scenario": scenario,
                "changes": changes,
                "result": effect,
                "guards": {
                    name: value for name, value in before.items() if name not in {change["path"] for change in changes}
                },
            }
            dump(manifest_path, manifest)
        target = self.outputs / "plans" / scenario
        stage = base / "stage" / "plans" / scenario
        # Immutable read inputs must still match even after a process restart.
        for name, expected in manifest.get("guards", {}).items():
            if digest(target / name) != expected:
                raise OperationError(
                    409, "effect_conflict", "The pending command belongs to a different planner state."
                )
        # Validate all files before any write. Allow the command's already-published files.
        for change in manifest["changes"]:
            current = digest(target / change["path"])
            if current not in (change["before"], change["after"]):
                raise OperationError(
                    409, "effect_conflict", "Planner files changed during reconciliation; human review required."
                )
            if digest(stage / change["path"]) != change["after"]:
                raise OperationError(503, "effect_corrupt", "The pending planner result needs human review.")
        for change in manifest["changes"]:
            dest = target / change["path"]
            if digest(dest) == change["after"]:
                continue
            if change["after"] is None:
                dest.unlink(missing_ok=True)
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            temp = dest.with_suffix(dest.suffix + ".daybreak-tmp")
            with (stage / change["path"]).open("rb") as src, temp.open("wb") as out:
                shutil.copyfileobj(src, out)
                out.flush()
                os.fsync(out.fileno())
            os.replace(temp, dest)
        return {
            **manifest["result"],
            "plan_id": (read_json(target / "plan.json") or {}).get("plan_id"),
            "effect_verified": True,
        }
