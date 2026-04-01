"""FastAPI app entrypoint for Canvas Chat."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from canvas_chat_2.api.db import init_db
from canvas_chat_2.api.routes_chat import router as chat_router
from canvas_chat_2.api.routes_graph import router as graph_router
from canvas_chat_2.api.settings import get_settings


def create_app() -> FastAPI:
    """Build and configure the FastAPI application.

    :returns: Configured FastAPI app instance.
    """

    settings = get_settings()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        """Initialize API resources on startup.

        :yields None: Lifespan control to FastAPI after startup init.
        """

        init_db()
        yield

    app = FastAPI(title="Canvas Chat API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        """Return a simple liveness payload.

        :returns: API liveness status.
        """

        return {"status": "ok"}

    app.include_router(graph_router)
    app.include_router(chat_router)
    return app


app = create_app()


def run() -> None:
    """Run the API server with uvicorn."""

    uvicorn.run("canvas_chat_2.api.main:app", host="127.0.0.1", port=8000, reload=True)
