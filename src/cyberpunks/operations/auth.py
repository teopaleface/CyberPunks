"""Autentificare server-la-server înainte de parsarea identității."""

import hmac
import os

from fastapi import Header, HTTPException
from pydantic import ValidationError

from cyberpunks.operations.models import Actor


def require_actor(
    authorization: str | None = Header(default=None),
    x_daybreak_actor: str | None = Header(default=None),
) -> Actor:
    token = os.environ.get("DAYBREAK_INTERNAL_TOKEN", "")
    if not token:
        raise HTTPException(
            503, detail={"code": "service_unconfigured", "message": "Internal authentication unavailable."}
        )
    if not authorization or not hmac.compare_digest(authorization.encode(), ("Bearer " + token).encode()):
        raise HTTPException(
            401, detail={"code": "unauthenticated", "message": "Trusted service authentication required."}
        )
    if not x_daybreak_actor or len(x_daybreak_actor) > 16000:
        raise HTTPException(401, detail={"code": "invalid_actor", "message": "Verified membership required."})
    try:
        return Actor.model_validate_json(x_daybreak_actor)
    except ValidationError:
        raise HTTPException(401, detail={"code": "invalid_actor", "message": "Verified membership required."}) from None


# The conversation router uses this same dependency.
get_actor = require_actor
