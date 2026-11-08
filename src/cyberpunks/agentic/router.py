"""Mount create_router(operations, store); authentication reuses require_actor.

GET reads snapshots; resume passively observes saved effects.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response

from cyberpunks.operations.auth import require_actor
from cyberpunks.operations.models import Actor, OperationError

from .contracts import TaskRequest, TaskView
from .coordinator import AgenticCoordinator


def create_router(operations, store):
    router = APIRouter(prefix="/api/conversation/tasks", tags=["agentic"])

    def safe(call):
        try:
            return call()
        except OperationError as exc:
            raise HTTPException(exc.status_code, detail={"code": exc.code, "message": exc.message}) from None
        except PermissionError:
            raise HTTPException(404, "Task unavailable") from None
        except ValueError:
            raise HTTPException(409, "Task data changed or is invalid. Start a fresh task.") from None

    def read(actor, task_id, scenario):
        operations.context(actor, scenario)
        task = store.get(actor, task_id)
        if task.scenario != scenario:
            raise HTTPException(404, "Task unavailable")
        context = operations.context(actor, task.scenario)
        current_cases = {case["case_id"]: case.get("version") for case in context.get("cases", [])}
        if any(current_cases.get(case["case_id"]) != case.get("version") for case in task.result.get("cases", [])):
            raise HTTPException(409, "Case changed. Start a fresh task.")
        if str(context["plan"]["version"]) != task.plan_version:
            # A confirmed operation may itself change the plan. Its immutable effect remains observable.
            effect = operations.observe_effect(actor, task.proposal["proposal_id"], scenario) if task.proposal else None
            if not effect or not effect.get("command"):
                raise HTTPException(409, "Snapshot is outdated. Start a fresh task.")
            task = task.model_copy(update={"result": {**task.result, "snapshot_outdated": True}})
        return task

    @router.post("", response_model=TaskView)
    def create(request: TaskRequest, response: Response, actor: Annotated[Actor, Depends(require_actor)] = None):
        response.headers["Cache-Control"] = "private, no-store"
        return safe(lambda: AgenticCoordinator(operations, store).run(actor, request))

    @router.get("/{task_id}", response_model=TaskView)
    def get(
        task_id: str,
        response: Response,
        scenario: str = "demo-vara",
        actor: Annotated[Actor, Depends(require_actor)] = None,
    ):
        response.headers["Cache-Control"] = "private, no-store"
        return safe(lambda: read(actor, task_id, scenario))

    @router.post("/{task_id}/resume", response_model=TaskView)
    def resume(
        task_id: str,
        response: Response,
        scenario: str = "demo-vara",
        actor: Annotated[Actor, Depends(require_actor)] = None,
    ):
        response.headers["Cache-Control"] = "private, no-store"

        def observe():
            task = read(actor, task_id, scenario)
            if task.status == "awaiting_confirmation" and task.proposal:
                from .effects import observe_effect

                effect = observe_effect(operations, actor, task.proposal["proposal_id"], scenario)
                state = effect["status"]
                status = {
                    "succeeded": "completed",
                    "completed": "completed",
                    "failed": "failed",
                    "cancelled": "cancelled",
                    "reconciling": "needs_reconciliation",
                }.get(state, "awaiting_confirmation")
                reply = {
                    "completed": "The confirmed operation completed.",
                    "failed": "The operation failed. No retry was performed.",
                    "cancelled": "The operation was cancelled.",
                    "needs_reconciliation": "The effect needs review. No recovery was performed.",
                }.get(status, "Awaiting confirmation in the application. No operation was executed.")
                if status == task.status:
                    return task.model_copy(update={"reply": reply})
                return store.update(
                    actor, task_id, status=status, result={**task.result, "effect": effect}, reply=reply
                )
            if task.status in ("running", "queued"):
                request = store.request(actor, task_id)
                return AgenticCoordinator(operations, store).run(actor, request, task_id=task_id)
            if task.status == "failed":
                return task.model_copy(
                    update={"reply": "Execution was not resumed. Start a fresh task or review its current status."}
                )
            return task

        return safe(observe)

    return router
