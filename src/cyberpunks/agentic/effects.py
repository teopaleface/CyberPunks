"""Adapters reuse existing preparation; confirmation remains in the application."""


def prepare_operation(operations, actor, request, context):
    fresh = operations.context(actor, request.scenario)
    version = context.get("plan", {}).get("version")
    if version is None or fresh.get("plan", {}).get("version") != version:
        raise ValueError("Plan changed; obtain a fresh analysis")
    if request.goal != "prepare_operation" or request.action is None:
        raise ValueError("An operational action is required")
    data = dict(request.data)
    data["plan_version"] = version
    case_id = request.case_id or data.get("case_id")
    if request.case_id and data.get("case_id", request.case_id) != request.case_id:
        raise ValueError("Conflicting case identifiers")
    if case_id:
        case = next((c for c in context.get("cases", []) if c["case_id"] == case_id), None)
        current = next((c for c in fresh.get("cases", []) if c["case_id"] == case_id), None)
        if case is None or current is None or case.get("version") is None or case["version"] != current.get("version"):
            raise ValueError("Case changed or unavailable; obtain a fresh analysis")
        data["case_id"] = case_id
        data["case_version"] = case["version"]
    if request.request_key:
        if data.get("idempotency_key", request.request_key) != request.request_key:
            raise ValueError("Conflicting idempotency keys")
        data["idempotency_key"] = request.request_key
    return operations.prepare(actor, request.action, data, request.scenario)


def observe_effect(operations, actor, proposal_id, scenario):
    """Requires a service passive reader; command() may reconcile and is forbidden."""
    operations.context(actor, scenario)
    reader = getattr(operations, "observe_effect", None)
    if reader is None:
        raise NotImplementedError("OperationsService needs passive observe_effect(actor, proposal_id, scenario)")
    return reader(actor, proposal_id, scenario)
