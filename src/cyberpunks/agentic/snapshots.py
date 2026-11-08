"""Fresh, complete role-scoped operational snapshots."""

from copy import deepcopy


def authorized_snapshot(operations, actor, scenario):
    context = deepcopy(operations.context(actor, scenario))
    version = context["plan"]["version"]
    if not version:
        raise ValueError("Missing plan version")
    context["plan_version"] = version
    return context
