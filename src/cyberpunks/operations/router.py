"""API comun, montat de runtime; toate rutele cer autentificare de serviciu."""

from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from cyberpunks.operations.auth import require_actor
from cyberpunks.operations.models import Actor, OperationError, ProposalRequest
from cyberpunks.operations.service import OperationsService, get_service

router = APIRouter(prefix="/api/operations", tags=["operations"])
VerifiedActor = Annotated[Actor, Depends(require_actor)]
Service = Annotated[OperationsService, Depends(get_service)]


def safe(call: Callable):
    try:
        return call()
    except OperationError as exc:
        raise HTTPException(exc.status_code, detail={"code": exc.code, "message": exc.message}) from None


@router.get("/context")
def context(actor: VerifiedActor, service: Service, scenario: str = Query(default="demo-vara")):
    return safe(lambda: service.context(actor, scenario))


@router.get("/demo-bindings")
def bindings(actor: VerifiedActor, service: Service, scenario: str = "demo-vara"):
    def run():
        service._scope(actor, scenario)
        if actor.role != "dispatcher":
            raise OperationError(403, "forbidden", "Only a dispatcher can inspect administrative demo bindings.")
        return service.demo_bindings(scenario)

    return safe(run)


@router.post("/proposals")
def prepare(req: ProposalRequest, actor: VerifiedActor, service: Service):
    return safe(lambda: service.prepare(actor, req.action, req.data, req.scenario))


@router.post("/proposals/{proposal_id}/confirm")
def confirm(proposal_id: str, actor: VerifiedActor, service: Service):
    return safe(lambda: service.confirm(actor, proposal_id))


@router.get("/commands/{command_id}")
def command(command_id: str, actor: VerifiedActor, service: Service):
    return safe(lambda: service.command(actor, command_id))
