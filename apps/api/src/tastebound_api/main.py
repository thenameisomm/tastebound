from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from tastebound_api.db.database import dispose_db, get_engine, init_db
from tastebound_api.db.demo_seed import seed_demo
from tastebound_api.errors import AppError
from tastebound_api.llm.provider import get_provider
from tastebound_api.routes import arrivals, demo, destinations, markets, runs, workspaces
from tastebound_api.schemas import HealthResponse
from tastebound_api.settings import get_settings

logger = logging.getLogger("tastebound")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper())
    await init_db(settings)
    await seed_demo()
    yield
    await dispose_db()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="TasteBound API",
        version=settings.version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url=None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status, content=exc.problem())

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        location = ".".join(str(part) for part in first.get("loc", []))
        message = first.get("msg", "Invalid request")
        detail = f"{location}: {message}" if location else str(message)
        return JSONResponse(
            status_code=422,
            content={
                "type": "about:blank",
                "title": "Validation failed",
                "status": 422,
                "detail": detail,
                "code": "validation_error",
            },
        )

    @app.get("/health", response_model=HealthResponse, tags=["health"])
    async def health() -> HealthResponse:
        db_status = "ok"
        try:
            engine = get_engine()
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("db health check failed: %s", exc)
            db_status = "error"
        qloo_status = "configured" if settings.qloo_api_key else "unconfigured"
        provider = get_provider(settings)
        llm_payload = {
            "provider": provider.name if provider else settings.llm_provider,
            "model": provider.model if provider else settings.ollama_model,
            "tools_ok": provider is not None and settings.llm_tool_calling,
        }
        return HealthResponse(
            status="ok" if db_status == "ok" else "degraded",
            db=db_status,
            qloo=qloo_status,
            llm=llm_payload,
            version=settings.version,
        )

    for router in (
        workspaces.router,
        markets.router,
        destinations.router,
        destinations.search_router,
        arrivals.router,
        runs.router,
        runs.briefs_router,
        demo.router,
    ):
        app.include_router(router)

    return app


app = create_app()
