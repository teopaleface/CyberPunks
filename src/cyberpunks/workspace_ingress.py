"""Restricted tunnel entrypoint. Run on loopback port 8723, never the runtime port."""

import re

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response

from cyberpunks.operations.auth import require_actor
from cyberpunks.operations.bindings import DEMO_ORGANIZATION

ID = r"[A-Za-z0-9_-]{1,160}"
UUID = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-8][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}"
LEGACY = frozenset(
    [
        "health",
        "scenarios",
        "plan",
        "work-items",
        "audit",
        "decision-titles",
        "metrics",
        "quarantine",
        "alerts",
        "notifications",
        "report",
        "posts",
        "plan/approval",
        "approvals",
        "labels",
        "rules",
        "run-info",
        "remedies",
    ]
)


def allowed(path: str, method: str) -> bool:
    patterns = {
        "GET": [
            rf"/operations/photos/{UUID}",
            r"/operations/context",
            rf"/operations/commands/{ID}",
            rf"/operations/proposals/{UUID}",
            rf"/conversation/tasks/{ID}",
        ],
        "DELETE": [rf"/operations/photos/{UUID}"],
        "POST": [
            r"/operations/work-items/[A-Za-z0-9_.-]{1,120}/photos",
            r"/operations/proposals",
            rf"/operations/proposals/{ID}/confirm",
            rf"/operations/commands/{ID}/recover",
            r"/conversation/(chat|voice-session|tasks)",
            rf"/conversation/tasks/{ID}/resume",
            rf"/conversation/tasks/{ID}/recommendations/{ID}/prepare",
        ],
    }
    return any(re.fullmatch(p, path) for p in patterns.get(method, []))


def legacy(path: str, method: str) -> bool:
    return method == "GET" and (
        path[1:] in LEGACY
        or bool(re.fullmatch(rf"/(work-items|series|posts)/[A-Za-z0-9_.-]{{1,160}}|/work-orders/{ID}\.pdf", path))
    )


def create_app(*, transport: httpx.AsyncBaseTransport | None = None) -> FastAPI:
    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
    async def ingress(request: Request, path: str):
        if request.url.path == "/healthz" and request.method == "GET":
            return JSONResponse({"status": "ok"})
        actor = require_actor(request.headers.get("authorization"), request.headers.get("x-daybreak-actor"))
        if not path.startswith("api/"):
            raise HTTPException(404, "Endpoint unavailable")
        target = "/" + path[4:]
        if not allowed(target, request.method) and not legacy(target, request.method):
            raise HTTPException(404, "Endpoint unavailable")
        if legacy(target, request.method) and (
            actor.role != "dispatcher"
            or actor.organization_id != DEMO_ORGANIZATION
            or "view_console" not in actor.permissions
        ):
            raise HTTPException(403, "Dispatcher membership required")
        if legacy(target, request.method) and request.query_params.get("scenario", "demo-vara") != "demo-vara":
            raise HTTPException(403, "Scenario unavailable")
        if any(k not in {"scenario", "source", "work_item_id"} for k in request.query_params):
            raise HTTPException(422, "Unsupported query")
        limit = (
            5 * 1024 * 1024 if re.fullmatch(r"/operations/work-items/[A-Za-z0-9_.-]{1,120}/photos", target) else 65000
        )
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > limit:
                raise HTTPException(413, "Request too large")
        headers = {
            k: v for k, v in request.headers.items() if k in {"authorization", "x-daybreak-actor", "content-type"}
        }
        try:
            async with httpx.AsyncClient(
                transport=transport, follow_redirects=False, trust_env=False, timeout=125
            ) as client:
                result = await client.request(
                    request.method,
                    "http://127.0.0.1:8720/api" + target,
                    params=request.query_params,
                    content=bytes(body),
                    headers=headers,
                )
            if result.status_code >= 300:
                return JSONResponse(
                    {"detail": "Upstream request failed"},
                    status_code=result.status_code if result.status_code >= 400 else 502,
                )
            return Response(
                result.content,
                status_code=result.status_code,
                headers={
                    "content-type": result.headers.get("content-type", "application/json"),
                    "cache-control": "no-store",
                },
            )
        except httpx.HTTPError:
            return JSONResponse({"detail": "Service unavailable"}, status_code=503)

    return app


app = create_app()
