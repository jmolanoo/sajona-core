from typing import Annotated

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from sajona_core.application.auth_service import AuthService
from sajona_core.application.produccion_service import ProduccionService
from sajona_core.application.sync_service import SyncService
from sajona_core.config import get_settings
from sajona_core.domain.entities import Usuario
from sajona_core.domain.exceptions import AuthenticationError
from sajona_core.infrastructure.audit_logger import DualAuditLogger
from sajona_core.infrastructure.database import get_db_session
from sajona_core.infrastructure.repositories import (
    SqlAlchemyAuthRepository,
    SqlAlchemyCoreRepository,
)
from sajona_core.infrastructure.security import Argon2PasswordHasher, JwtTokenProvider

bearer_scheme = HTTPBearer(auto_error=False)


def get_correlation_id(
    request: Request,
    x_correlation_id: Annotated[str | None, Header()] = None,
) -> str:
    return str(x_correlation_id or getattr(request.state, "correlation_id", "unknown"))


def get_audit_logger(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DualAuditLogger:
    return DualAuditLogger(session, get_settings().audit_log_dir)


def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    audit: Annotated[DualAuditLogger, Depends(get_audit_logger)],
) -> AuthService:
    settings = get_settings()
    return AuthService(
        repo=SqlAlchemyAuthRepository(session),
        hasher=Argon2PasswordHasher(),
        tokens=JwtTokenProvider(),
        audit=audit,
        access_minutes=settings.access_token_minutes,
        refresh_days=settings.refresh_token_days,
    )


def get_produccion_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    audit: Annotated[DualAuditLogger, Depends(get_audit_logger)],
) -> ProduccionService:
    return ProduccionService(repo=SqlAlchemyCoreRepository(session), audit=audit)


def get_sync_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    produccion: Annotated[ProduccionService, Depends(get_produccion_service)],
) -> SyncService:
    return SyncService(repo=SqlAlchemyCoreRepository(session), produccion=produccion)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Usuario:
    if credentials is None or not credentials.credentials:
        raise AuthenticationError("Token Bearer requerido.")
    payload = JwtTokenProvider().decode_access_token(credentials.credentials)
    user_id = str(payload.get("sub", ""))
    user = await SqlAlchemyAuthRepository(session).get_user_by_id(user_id)
    if user is None or not user.is_active:
        raise AuthenticationError("Usuario inactivo o no autorizado.")
    return user
