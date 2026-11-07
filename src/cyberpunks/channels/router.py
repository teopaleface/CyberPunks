"""API same-origin prin proxy-ul Next autentificat. Nu montează confirmări de operații."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Response

from cyberpunks.channels.conversation import ConversationService
from cyberpunks.channels.elevenlabs import ElevenLabs
from cyberpunks.channels.limits import limits
from cyberpunks.channels.models import ChannelError, ChatRequest, VoiceRequest

router = APIRouter(prefix="/api/conversation", tags=["conversation"])


async def trusted_actor(authorization: str | None = None, x_daybreak_actor: str | None = None):
    # The actual dependency is wrapped below with explicit Header parameters. Lazy import lets root
    # mount this router while the parallel operations package is still being implemented.
    from cyberpunks.operations.auth import require_actor

    return require_actor(authorization=authorization, x_daybreak_actor=x_daybreak_actor)


async def get_actor(
    authorization: str | None = Header(default=None),
    x_daybreak_actor: str | None = Header(default=None),
):
    return await trusted_actor(authorization, x_daybreak_actor)


def get_conversation() -> ConversationService:
    from cyberpunks.operations.service import get_service

    return ConversationService(get_service())


def channel_http_error(exc: ChannelError) -> HTTPException:
    return HTTPException(
        exc.status_code,
        detail={"code": exc.code, "message": exc.message},
        headers={"Retry-After": "60"} if exc.status_code == 429 else None,
    )


def operation_http_error(exc: Exception) -> HTTPException:
    from cyberpunks.operations.models import OperationError

    if isinstance(exc, OperationError):
        return HTTPException(exc.status_code, detail={"code": exc.code, "message": exc.message})
    return HTTPException(
        503,
        detail={
            "code": "conversation_unavailable",
            "message": "The conversation service is unavailable. No action was executed.",
        },
    )


@router.post("/chat")
async def chat(
    request: ChatRequest,
    response: Response,
    actor: Annotated[Any, Depends(get_actor)],
    conversation: Annotated[ConversationService, Depends(get_conversation)],
):
    response.headers["Cache-Control"] = "no-store"
    try:
        async with limits.acquire((actor.organization_id, actor.user_id)):
            return await conversation.chat(actor, request)
    except ChannelError as exc:
        raise channel_http_error(exc) from None
    except Exception as exc:  # noqa: BLE001 - public boundary must not leak private provider objects.
        raise operation_http_error(exc) from None


@router.post("/voice-session")
async def voice_session(
    request: VoiceRequest,
    response: Response,
    actor: Annotated[Any, Depends(get_actor)],
    conversation: Annotated[ConversationService, Depends(get_conversation)],
):
    response.headers["Cache-Control"] = "no-store"
    try:
        # Validate membership/scenario through the same source of truth before issuing a token.
        conversation.operations.context(actor, request.scenario)
        async with limits.acquire((actor.organization_id, actor.user_id), voice=True):
            return await ElevenLabs().session(actor.role)
    except ChannelError as exc:
        raise channel_http_error(exc) from None
    except Exception as exc:  # noqa: BLE001 - public boundary must not leak private provider objects.
        raise operation_http_error(exc) from None


from cyberpunks.channels.whatsapp import router as whatsapp_router

router.include_router(whatsapp_router)
