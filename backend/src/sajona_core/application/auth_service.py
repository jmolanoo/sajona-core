import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from sajona_core.application.dto import (
    AdminUserCreateDTO,
    AdminUserUpdateDTO,
    LoginRequest,
    LoginResponse,
    PasswordResetConfirmDTO,
    PasswordResetRequestDTO,
    UserProfileDTO,
)
from sajona_core.application.ports import (
    AuditLoggerPort,
    AuthRepositoryPort,
    PasswordHasherPort,
    TokenProviderPort,
)
from sajona_core.application.rbac import ENTITY_PERMISSIONS, require_admin
from sajona_core.domain.entities import AuditLogEntry, Funcionario, Usuario
from sajona_core.domain.enums import RoleName
from sajona_core.domain.exceptions import AuthenticationError, EntityNotFoundError


def _build_permissions_map(role: RoleName) -> dict[str, list[str]]:
    return {
        entity: sorted(perms_by_role.get(role, set()))
        for entity, perms_by_role in ENTITY_PERMISSIONS.items()
    }


def _to_profile(user: Usuario, full_name: str) -> UserProfileDTO:
    return UserProfileDTO(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        full_name=full_name,
        funcionario_id=user.funcionario_id,
        is_active=user.is_active,
        must_change_password=user.must_change_password,
        permissions=_build_permissions_map(user.role),
    )


class AuthService:
    def __init__(
        self,
        repo: AuthRepositoryPort,
        hasher: PasswordHasherPort,
        tokens: TokenProviderPort,
        audit: AuditLoggerPort,
        *,
        access_minutes: int = 15,
        refresh_days: int = 7,
    ) -> None:
        self._repo = repo
        self._hasher = hasher
        self._tokens = tokens
        self._audit = audit
        self._access_seconds = access_minutes * 60
        self._refresh_days = refresh_days

    async def login(
        self, payload: LoginRequest, correlation_id: str
    ) -> tuple[LoginResponse, str]:
        user = await self._repo.get_user_by_identifier(payload.identifier.strip().lower())
        if user is None or not user.is_active:
            raise AuthenticationError("Usuario inexistente o desactivado.")
        if not self._hasher.verify_password(payload.password, user.password_hash):
            await self._audit_auth(user.username, user.role.value, "LOGIN_FAILED", correlation_id)
            raise AuthenticationError("Usuario o contraseña incorrectos.")

        access = self._tokens.create_access_token(user)
        raw_refresh, refresh_hash = self._tokens.generate_refresh_token()
        expires = datetime.now(UTC) + timedelta(days=self._refresh_days)
        await self._repo.store_refresh_token(str(uuid4()), user.id, refresh_hash, expires)
        await self._audit_auth(user.username, user.role.value, "LOGIN", correlation_id, user.id)
        resp = LoginResponse(
            access_token=access,
            expires_in=self._access_seconds,
            user=_to_profile(user, user.username),
        )
        return resp, raw_refresh

    async def refresh(
        self, raw_refresh: str | None, correlation_id: str
    ) -> tuple[LoginResponse, str]:
        if not raw_refresh:
            raise AuthenticationError("Refresh token ausente.")
        token_hash = self._tokens.hash_refresh_token(raw_refresh)
        stored = await self._repo.get_refresh_token(token_hash)
        if stored is None:
            raise AuthenticationError("Refresh token inválido.")
        if stored["revoked"]:
            await self._repo.revoke_all_user_refresh_tokens(str(stored["user_id"]))
            raise AuthenticationError("Reuso detectado: sesiones revocadas por seguridad.")
        expires_at: datetime = stored["expires_at"]
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at < datetime.now(UTC):
            raise AuthenticationError("Refresh token expirado.")

        await self._repo.revoke_refresh_token(str(stored["id"]))
        user = await self._repo.get_user_by_id(str(stored["user_id"]))
        if user is None or not user.is_active:
            raise AuthenticationError("Usuario inactivo.")

        new_access = self._tokens.create_access_token(user)
        new_raw_refresh, new_hash = self._tokens.generate_refresh_token()
        new_exp = datetime.now(UTC) + timedelta(days=self._refresh_days)
        await self._repo.store_refresh_token(str(uuid4()), user.id, new_hash, new_exp)
        await self._audit_auth(
            user.username, user.role.value, "TOKEN_REFRESH", correlation_id, user.id
        )
        return (
            LoginResponse(
                access_token=new_access,
                expires_in=self._access_seconds,
                user=_to_profile(user, user.username),
            ),
            new_raw_refresh,
        )

    async def logout(self, raw_refresh: str | None) -> None:
        if not raw_refresh:
            return
        stored = await self._repo.get_refresh_token(self._tokens.hash_refresh_token(raw_refresh))
        if stored:
            await self._repo.revoke_refresh_token(str(stored["id"]))

    async def get_profile(self, user_id: str) -> UserProfileDTO:
        user = await self._repo.get_user_by_id(user_id)
        if user is None:
            raise EntityNotFoundError("Usuario", user_id)
        return _to_profile(user, user.username)

    async def request_password_reset(
        self, payload: PasswordResetRequestDTO, correlation_id: str
    ) -> dict[str, str]:
        user = await self._repo.get_user_by_identifier(payload.email.strip().lower())
        if user is None:
            return {"message": "Si el correo existe, recibirá instrucciones de restablecimiento."}
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        exp = datetime.now(UTC) + timedelta(minutes=30)
        await self._repo.create_password_reset_token(str(uuid4()), user.id, token_hash, exp)
        await self._audit_auth(
            user.username, user.role.value, "PASSWORD_RESET_REQUEST", correlation_id, user.id
        )
        return {
            "message": "Token de recuperación generado.",
            "recovery_token": raw_token,
        }

    async def confirm_password_reset(
        self, payload: PasswordResetConfirmDTO, correlation_id: str
    ) -> dict[str, str]:
        token_hash = hashlib.sha256(payload.token.encode()).hexdigest()
        user_id = await self._repo.consume_password_reset_token(token_hash)
        if user_id is None:
            raise AuthenticationError("Token de recuperación inválido o expirado.")
        user = await self._repo.get_user_by_id(user_id)
        if user is None:
            raise EntityNotFoundError("Usuario", user_id)
        user.password_hash = self._hasher.hash_password(payload.new_password)
        user.must_change_password = False
        user.version += 1
        await self._repo.update_user(user)
        await self._repo.revoke_all_user_refresh_tokens(user.id)
        await self._audit_auth(
            user.username, user.role.value, "PASSWORD_RESET_CONFIRM", correlation_id, user.id
        )
        return {"message": "Contraseña actualizada exitosamente."}

    async def list_users_admin(self, actor_role: RoleName) -> list[dict[str, Any]]:
        require_admin(actor_role)
        return await self._repo.list_users()

    async def create_user_admin(
        self,
        actor: Usuario,
        payload: AdminUserCreateDTO,
        correlation_id: str,
    ) -> dict[str, Any]:
        require_admin(actor.role)
        func_id = str(uuid4())
        user_id = str(uuid4())
        func = Funcionario(
            id=func_id,
            nombre=payload.nombre,
            apellido=payload.apellido,
            documento=payload.documento,
            email=payload.email.lower(),
            telefono=payload.telefono,
            cargo=payload.cargo,
        )
        user = Usuario(
            id=user_id,
            username=payload.username.lower(),
            email=payload.email.lower(),
            password_hash=self._hasher.hash_password(payload.password),
            role=payload.role,
            funcionario_id=func_id,
            is_active=True,
        )
        created = await self._repo.create_user(user, func)
        await self._audit.log(
            AuditLogEntry(
                id=str(uuid4()),
                correlation_id=correlation_id,
                user_id=actor.id,
                username=actor.username,
                role=actor.role.value,
                entity_type="usuarios",
                entity_id=created.id,
                action="CREATE",
                source="online",
                result="SUCCESS",
                after_state={"username": created.username, "role": created.role.value},
            )
        )
        return _to_profile(created, f"{payload.nombre} {payload.apellido}").model_dump()

    async def update_user_admin(
        self,
        actor: Usuario,
        target_id: str,
        payload: AdminUserUpdateDTO,
        correlation_id: str,
    ) -> dict[str, Any]:
        require_admin(actor.role)
        user = await self._repo.get_user_by_id(target_id)
        if user is None:
            raise EntityNotFoundError("Usuario", target_id)
        if payload.role is not None:
            user.role = payload.role
        if payload.is_active is not None:
            user.is_active = payload.is_active
        if payload.reset_password:
            user.password_hash = self._hasher.hash_password(payload.reset_password)
            await self._repo.revoke_all_user_refresh_tokens(user.id)
        user.version += 1
        updated = await self._repo.update_user(user)
        await self._audit.log(
            AuditLogEntry(
                id=str(uuid4()),
                correlation_id=correlation_id,
                user_id=actor.id,
                username=actor.username,
                role=actor.role.value,
                entity_type="usuarios",
                entity_id=updated.id,
                action="UPDATE",
                source="online",
                result="SUCCESS",
                after_state={"role": updated.role.value, "is_active": updated.is_active},
            )
        )
        return _to_profile(updated, updated.username).model_dump()

    async def _audit_auth(
        self,
        username: str,
        role: str,
        action: str,
        correlation_id: str,
        user_id: str | None = None,
    ) -> None:
        await self._audit.log(
            AuditLogEntry(
                id=str(uuid4()),
                correlation_id=correlation_id,
                user_id=user_id,
                username=username,
                role=role,
                entity_type="auth",
                entity_id=user_id or username,
                action=action,
                source="online",
                result="SUCCESS" if action != "LOGIN_FAILED" else "DENIED",
            )
        )
