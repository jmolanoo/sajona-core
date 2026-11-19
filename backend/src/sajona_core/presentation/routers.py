from datetime import UTC, date, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Cookie, Depends, Header, Query, Request, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from sajona_core.application.auth_service import AuthService
from sajona_core.application.dto import (
    AdminUserCreateDTO,
    AdminUserUpdateDTO,
    LoginRequest,
    LoginResponse,
    PasswordResetConfirmDTO,
    PasswordResetRequestDTO,
    SyncPushRequest,
    SyncPushResponse,
    UserProfileDTO,
)
from sajona_core.application.produccion_service import ProduccionService
from sajona_core.application.rbac import require_admin
from sajona_core.application.sync_service import SyncService
from sajona_core.config import get_settings
from sajona_core.domain.entities import Usuario
from sajona_core.infrastructure.audit_logger import DualAuditLogger
from sajona_core.infrastructure.database import get_db_session
from sajona_core.presentation.dependencies import (
    get_audit_logger,
    get_auth_service,
    get_correlation_id,
    get_current_user,
    get_produccion_service,
    get_sync_service,
)

health_router = APIRouter(tags=["Salud"])
auth_router = APIRouter(prefix="/api/v1/auth", tags=["Autenticación"])
dashboard_router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])
entity_router = APIRouter(prefix="/api/v1/entities", tags=["Módulos Núcleo"])
lotes_router = APIRouter(prefix="/api/v1/lotes", tags=["Trazabilidad Lote"])
sync_router = APIRouter(prefix="/api/v1/sync", tags=["Sincronización Offline-First"])
admin_router = APIRouter(prefix="/api/v1/admin", tags=["Administración y Auditoría"])


def _set_refresh_cookie(request: Request, response: Response, raw_token: str) -> None:
    settings = get_settings()
    is_https = (
        request.url.scheme == "https"
        or request.headers.get("x-forwarded-proto", "").lower() == "https"
    )
    response.set_cookie(
        key="sajona_core_refresh",
        value=raw_token,
        httponly=True,
        secure=settings.cookie_secure and is_https,
        samesite="lax",
        path="/api/v1/auth",
        max_age=settings.refresh_token_days * 86400,
    )


@health_router.get("/health")
@health_router.get("/api/v1/health")
async def healthcheck(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, Any]:
    await session.execute(text("SELECT 1"))
    return {
        "status": "healthy",
        "database": "connected",
        "version": get_settings().app_version,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@auth_router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    correlation_id: Annotated[str, Depends(get_correlation_id)],
    svc: Annotated[AuthService, Depends(get_auth_service)],
) -> LoginResponse:
    res, raw_refresh = await svc.login(payload, correlation_id)
    _set_refresh_cookie(request, response, raw_refresh)
    return res


@auth_router.post("/refresh", response_model=LoginResponse)
async def refresh_token(
    request: Request,
    response: Response,
    correlation_id: Annotated[str, Depends(get_correlation_id)],
    svc: Annotated[AuthService, Depends(get_auth_service)],
    sajona_core_refresh: Annotated[str | None, Cookie()] = None,
) -> LoginResponse:
    res, new_raw = await svc.refresh(sajona_core_refresh, correlation_id)
    _set_refresh_cookie(request, response, new_raw)
    return res


@auth_router.post("/logout")
async def logout(
    response: Response,
    svc: Annotated[AuthService, Depends(get_auth_service)],
    sajona_core_refresh: Annotated[str | None, Cookie()] = None,
) -> dict[str, str]:
    await svc.logout(sajona_core_refresh)
    response.delete_cookie("sajona_core_refresh", path="/api/v1/auth")
    return {"message": "Sesión cerrada correctamente."}


@auth_router.get("/me", response_model=UserProfileDTO)
async def get_me(
    user: Annotated[Usuario, Depends(get_current_user)],
    svc: Annotated[AuthService, Depends(get_auth_service)],
) -> UserProfileDTO:
    return await svc.get_profile(user.id)


@auth_router.post("/password-reset/request")
async def request_reset(
    payload: PasswordResetRequestDTO,
    correlation_id: Annotated[str, Depends(get_correlation_id)],
    svc: Annotated[AuthService, Depends(get_auth_service)],
) -> dict[str, str]:
    return await svc.request_password_reset(payload, correlation_id)


@auth_router.post("/password-reset/confirm")
async def confirm_reset(
    payload: PasswordResetConfirmDTO,
    correlation_id: Annotated[str, Depends(get_correlation_id)],
    svc: Annotated[AuthService, Depends(get_auth_service)],
) -> dict[str, str]:
    return await svc.confirm_password_reset(payload, correlation_id)


@dashboard_router.get("/summary")
async def dashboard_summary(
    user: Annotated[Usuario, Depends(get_current_user)],
    svc: Annotated[ProduccionService, Depends(get_produccion_service)],
    fecha_inicio: Annotated[date | None, Query()] = None,
    fecha_fin: Annotated[date | None, Query()] = None,
    variedad_id: Annotated[str | None, Query()] = None,
    tipo_propagacion: Annotated[str | None, Query()] = None,
) -> dict[str, Any]:
    return await svc.get_dashboard_summary(
        user,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        variedad_id=variedad_id,
        tipo_propagacion=tipo_propagacion,
    )


@lotes_router.get("/{lote_id}/trazabilidad")
async def lote_traceability(
    lote_id: str,
    user: Annotated[Usuario, Depends(get_current_user)],
    svc: Annotated[ProduccionService, Depends(get_produccion_service)],
) -> dict[str, Any]:
    return await svc.get_traceability(user, lote_id)


@entity_router.get("/{entity_type}")
async def list_entities(
    entity_type: str,
    user: Annotated[Usuario, Depends(get_current_user)],
    svc: Annotated[ProduccionService, Depends(get_produccion_service)],
    lote_id: Annotated[str | None, Query()] = None,
    transplante_id: Annotated[str | None, Query()] = None,
    lote_madre_id: Annotated[str | None, Query()] = None,
) -> list[dict[str, Any]]:
    return await svc.list_records(
        user,
        entity_type,
        lote_id=lote_id,
        transplante_id=transplante_id,
        lote_madre_id=lote_madre_id,
    )


@entity_router.post("/{entity_type}", status_code=201)
async def create_entity(
    entity_type: str,
    payload: dict[str, Any],
    correlation_id: Annotated[str, Depends(get_correlation_id)],
    user: Annotated[Usuario, Depends(get_current_user)],
    svc: Annotated[ProduccionService, Depends(get_produccion_service)],
) -> dict[str, Any]:
    return await svc.create_or_update(
        user, entity_type, payload, correlation_id=correlation_id
    )


@entity_router.put("/{entity_type}/{entity_id}")
async def update_entity(
    entity_type: str,
    entity_id: str,
    payload: dict[str, Any],
    correlation_id: Annotated[str, Depends(get_correlation_id)],
    user: Annotated[Usuario, Depends(get_current_user)],
    svc: Annotated[ProduccionService, Depends(get_produccion_service)],
    if_match_version: Annotated[int | None, Header()] = None,
) -> dict[str, Any]:
    expected_v = if_match_version or payload.get("version")
    return await svc.create_or_update(
        user,
        entity_type,
        payload,
        entity_id=entity_id,
        expected_version=int(expected_v) if expected_v is not None else None,
        correlation_id=correlation_id,
    )


@entity_router.delete("/{entity_type}/{entity_id}")
async def delete_entity(
    entity_type: str,
    entity_id: str,
    correlation_id: Annotated[str, Depends(get_correlation_id)],
    user: Annotated[Usuario, Depends(get_current_user)],
    svc: Annotated[ProduccionService, Depends(get_produccion_service)],
    version: Annotated[int | None, Query()] = None,
) -> dict[str, Any]:
    return await svc.delete_record(
        user,
        entity_type,
        entity_id,
        expected_version=version,
        correlation_id=correlation_id,
    )


@sync_router.post("/push", response_model=SyncPushResponse)
async def sync_push(
    payload: SyncPushRequest,
    correlation_id: Annotated[str, Depends(get_correlation_id)],
    user: Annotated[Usuario, Depends(get_current_user)],
    svc: Annotated[SyncService, Depends(get_sync_service)],
) -> SyncPushResponse:
    return await svc.push(user, payload.mutations, correlation_id)


@sync_router.get("/pull")
async def sync_pull(
    user: Annotated[Usuario, Depends(get_current_user)],
    svc: Annotated[SyncService, Depends(get_sync_service)],
    since: Annotated[datetime | None, Query()] = None,
) -> dict[str, Any]:
    return await svc.pull(user, since)


@admin_router.get("/users")
async def list_admin_users(
    user: Annotated[Usuario, Depends(get_current_user)],
    svc: Annotated[AuthService, Depends(get_auth_service)],
) -> list[dict[str, Any]]:
    return await svc.list_users_admin(user.role)


@admin_router.post("/users", status_code=201)
async def create_admin_user(
    payload: AdminUserCreateDTO,
    correlation_id: Annotated[str, Depends(get_correlation_id)],
    user: Annotated[Usuario, Depends(get_current_user)],
    svc: Annotated[AuthService, Depends(get_auth_service)],
) -> dict[str, Any]:
    return await svc.create_user_admin(user, payload, correlation_id)


@admin_router.patch("/users/{user_id}")
async def update_admin_user(
    user_id: str,
    payload: AdminUserUpdateDTO,
    correlation_id: Annotated[str, Depends(get_correlation_id)],
    user: Annotated[Usuario, Depends(get_current_user)],
    svc: Annotated[AuthService, Depends(get_auth_service)],
) -> dict[str, Any]:
    return await svc.update_user_admin(user, user_id, payload, correlation_id)


@admin_router.get("/audit-logs")
async def list_audit_logs(
    user: Annotated[Usuario, Depends(get_current_user)],
    audit: Annotated[DualAuditLogger, Depends(get_audit_logger)],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[dict[str, Any]]:
    require_admin(user.role)
    return await audit.list_recent(limit=limit)
