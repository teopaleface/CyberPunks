"""API comun, montat de runtime; toate rutele cer autentificare de serviciu."""

from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from starlette.concurrency import run_in_threadpool

from cyberpunks.operations.auth import require_actor
from cyberpunks.operations.models import Actor, OperationError, ProposalRequest, RecoveryRequest
from cyberpunks.operations.photos import FORMATS, MAX_BYTES
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


@router.get("/proposals/{proposal_id}")
def proposal(proposal_id: str, actor: VerifiedActor, service: Service):
    return safe(lambda: service.proposal(actor, proposal_id))


@router.post("/proposals/{proposal_id}/confirm")
def confirm(proposal_id: str, actor: VerifiedActor, service: Service):
    return safe(lambda: service.confirm(actor, proposal_id))


@router.get("/commands/{command_id}")
def command(command_id: str, actor: VerifiedActor, service: Service):
    return safe(lambda: service.command(actor, command_id))


@router.post("/commands/{command_id}/recover")
def recover(command_id: str, req: RecoveryRequest, actor: VerifiedActor, service: Service):
    return safe(lambda: service.recover(actor, command_id, req.decision, req.reason))


@router.post("/work-items/{work_item_id}/photos")
async def upload_photo(
    work_item_id: str, request: Request, actor: VerifiedActor, service: Service, scenario: str = "demo-vara"
):
    await run_in_threadpool(safe, lambda: service.authorize_photo_upload(actor, work_item_id, scenario))
    mime = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if mime not in FORMATS:
        raise HTTPException(415, detail={"code": "invalid_photo_type", "message": "Upload JPEG, PNG or WebP."})
    length = request.headers.get("content-length")
    if length and (len(length) > 10 or not length.isascii() or not length.isdecimal() or int(length) > MAX_BYTES):
        raise HTTPException(413, detail={"code": "photo_too_large", "message": "Photos must not exceed 5 MiB."})
    content = bytearray()
    async for chunk in request.stream():
        if len(content) + len(chunk) > MAX_BYTES:
            raise HTTPException(413, detail={"code": "photo_too_large", "message": "Photos must not exceed 5 MiB."})
        content.extend(chunk)
    return await run_in_threadpool(
        safe, lambda: service.upload_photo(actor, work_item_id, bytes(content), mime, scenario)
    )


@router.get("/photos/{photo_id}")
def read_photo(photo_id: str, actor: VerifiedActor, service: Service, scenario: str = "demo-vara"):
    metadata, content = safe(lambda: service.photo(actor, photo_id, scenario))
    return Response(
        content,
        media_type=metadata["mime_type"],
        headers={
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
            "Content-Disposition": "inline",
            "Cross-Origin-Resource-Policy": "same-origin",
        },
    )


@router.delete("/photos/{photo_id}")
def delete_photo(photo_id: str, actor: VerifiedActor, service: Service, scenario: str = "demo-vara"):
    return safe(lambda: service.delete_photo(actor, photo_id, scenario))
