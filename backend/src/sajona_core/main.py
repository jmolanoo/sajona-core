from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from sajona_core.config import get_settings
from sajona_core.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessRuleViolationError,
    ConflictError,
    DomainError,
    EntityNotFoundError,
)
from sajona_core.infrastructure.database import SessionLocal, engine
from sajona_core.infrastructure.models import Base
from sajona_core.infrastructure.seed import run_seed_if_empty
from sajona_core.presentation.routers import (
    admin_router,
    auth_router,
    dashboard_router,
    entity_router,
    health_router,
    lotes_router,
    sync_router,
)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    if get_settings().seed_demo_data:
        async with SessionLocal() as session:
            await run_seed_if_empty(session)
    yield


def _status_for_error(exc: DomainError) -> int:
    if isinstance(exc, AuthenticationError):
        return 401
    if isinstance(exc, AuthorizationError):
        return 403
    if isinstance(exc, EntityNotFoundError):
        return 404
    if isinstance(exc, ConflictError):
        return 409
    if isinstance(exc, BusinessRuleViolationError):
        return 422
    return 400


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def correlation_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        cid = request.headers.get("X-Correlation-ID") or str(uuid4())
        request.state.correlation_id = cid
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = cid
        return response

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        cid = getattr(request.state, "correlation_id", "unknown")
        return JSONResponse(
            status_code=_status_for_error(exc),
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "correlation_id": cid,
                }
            },
        )

    for router in (
        health_router,
        auth_router,
        dashboard_router,
        entity_router,
        lotes_router,
        sync_router,
        admin_router,
    ):
        app.include_router(router)

    return app


app = create_app()
