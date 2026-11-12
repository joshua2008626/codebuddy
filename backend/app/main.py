"""FastAPI application factory."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import Settings, load_settings
from .db import create_tables, make_engine, make_session_factory
from .ratelimit import FailureThrottle, SlidingWindowLimiter
from .routers import ai, auth, challenges, execute, lessons, projects
from .routers.common import enforce_origin
from .services.judge0 import Judge0Client
from .services.llm import LlmClient

log = logging.getLogger("codebuddy")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()

    engine = make_engine(settings.database_url)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        create_tables(engine)  # creates missing tables; use migrations before changing the schema in production
        yield
        engine.dispose()

    app = FastAPI(
        title="CodeBuddy API",
        version="0.1.0",
        lifespan=lifespan,
        dependencies=[Depends(enforce_origin)],  # CSRF check for every state-changing route
        # Interactive docs are handy in development but are not exposed in production.
        docs_url=None if settings.is_production else "/api/docs",
        redoc_url=None,
        openapi_url=None if settings.is_production else "/api/openapi.json",
    )

    app.state.settings = settings
    app.state.engine = engine
    app.state.db_factory = make_session_factory(engine)
    app.state.login_throttle = FailureThrottle(settings.login_max_failures, settings.login_window_seconds)
    app.state.login_throttle_email = FailureThrottle(settings.login_max_failures * 4, settings.login_window_seconds)
    app.state.judge0 = Judge0Client(settings)
    app.state.llm = LlmClient(settings)
    app.state.limiters = {
        "execute": SlidingWindowLimiter(settings.rate_limit_execute_per_min),
        "ai": SlidingWindowLimiter(settings.rate_limit_ai_per_min),
        "submit": SlidingWindowLimiter(settings.rate_limit_submit_per_min),
        "auth": SlidingWindowLimiter(settings.rate_limit_auth_per_min),
        "projects": SlidingWindowLimiter(settings.rate_limit_projects_per_min),
    }

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,  # needed for the session cookie
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Content-Type"],
    )

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        return response

    @app.exception_handler(Exception)
    async def unhandled(_: Request, exc: Exception):
        # Log details server-side; never send stack traces or internals to the client.
        log.exception("Unhandled error", exc_info=exc)
        return JSONResponse(status_code=500, content={"detail": {"code": "internal_error", "message": "Something went wrong on our side."}})

    @app.get("/api/health", tags=["meta"])
    async def health():
        return {"status": "ok", "execution_configured": settings.execution_configured, "ai_configured": settings.ai_configured}

    app.include_router(execute.router)
    app.include_router(ai.router)
    app.include_router(challenges.router)
    app.include_router(auth.router)
    app.include_router(projects.router)
    app.include_router(lessons.router)
    return app


app = create_app()
