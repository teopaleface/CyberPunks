"""Private local API for the three-role Daybreak workspace.

Run through scripts/daybreak_runtime.py so credentials and output paths are
explicit. This factory leaves the existing API process and its data untouched.
"""

from __future__ import annotations

import hmac
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from cyberpunks.api import app as legacy
from cyberpunks.api.store import Store
from cyberpunks.common.paths import OUTPUTS


def create_app() -> FastAPI:
    from cyberpunks.channels.router import router as conversation_router
    from cyberpunks.operations.router import router as operations_router

    output_root = Path(os.environ.get("DAYBREAK_OPERATIONS_OUTPUTS", OUTPUTS / "operations-runtime" / "data"))
    legacy.store = Store(outputs=output_root)
    runtime = FastAPI(title="Daybreak private workspace", version="0.1.0")

    @runtime.middleware("http")
    async def require_internal_access(request: Request, call_next):
        if request.url.path.startswith("/api/"):
            token = os.environ.get("DAYBREAK_INTERNAL_TOKEN", "")
            if not token:
                return JSONResponse({"detail": "The private API is not configured."}, status_code=503)
            supplied = request.headers.get("authorization", "")
            if not hmac.compare_digest(supplied, f"Bearer {token}"):
                return JSONResponse({"detail": "Authentication required."}, status_code=401)
            # Old handlers write files without the common proposal/command ledger.
            # Keep them available only in the original API process, not this runtime.
            if request.method not in ("GET", "HEAD", "OPTIONS") and not request.url.path.startswith(
                ("/api/operations/", "/api/conversation/")
            ):
                return JSONResponse({"detail": "Use a confirmed workspace proposal for operational changes."}, status_code=409)
        response = await call_next(request)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @runtime.get("/healthz")
    def healthz():
        return {"status": "ok", "service": "daybreak-workspace", "private_api": True}

    runtime.include_router(legacy.api)
    runtime.include_router(operations_router)
    runtime.include_router(conversation_router)
    return runtime
