"""Public ingress for Meta only. Never expose the private workspace through a tunnel."""

from fastapi import FastAPI

from cyberpunks.channels.whatsapp import router


def create_app() -> FastAPI:
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.include_router(router, prefix="/api/conversation")
    return app
