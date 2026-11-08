"""Server-actor bridge for new channel integrations; existing channels are unchanged."""

from .contracts import TaskRequest
from .coordinator import AgenticCoordinator


def run_task(operations, store, actor, request: TaskRequest):
    task = AgenticCoordinator(operations, store).run(actor, request)
    operations.context(actor, request.scenario)
    owned = store.get(actor, task.task_id)
    if owned.scenario != request.scenario:
        raise ValueError("Task association mismatch")
    return {"reply": owned.reply[:240], "task_ref": owned.task_id}
