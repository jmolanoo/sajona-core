import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from sajona_core.config import get_settings
from sajona_core.domain.entities import Usuario
from sajona_core.domain.exceptions import AuthenticationError


class Argon2PasswordHasher:
    def __init__(self) -> None:
        self._pwd = PasswordHash.recommended()

    def hash_password(self, plain: str) -> str:
        return str(self._pwd.hash(plain))

    def verify_password(self, plain: str, hashed: str) -> bool:
        try:
            return bool(self._pwd.verify(plain, hashed))
        except Exception:
            return False


class JwtTokenProvider:
    def __init__(self) -> None:
        self._settings = get_settings()

    def create_access_token(self, user: Usuario) -> str:
        now = datetime.now(UTC)
        exp = now + timedelta(minutes=self._settings.access_token_minutes)
        payload: dict[str, Any] = {
            "sub": user.id,
            "username": user.username,
            "role": user.role.value,
            "exp": exp,
            "iat": now,
        }
        return str(
            jwt.encode(
                payload, self._settings.jwt_secret_key, algorithm=self._settings.jwt_algorithm
            )
        )

    def decode_access_token(self, token: str) -> dict[str, Any]:
        try:
            decoded: dict[str, Any] = jwt.decode(
                token,
                self._settings.jwt_secret_key,
                algorithms=[self._settings.jwt_algorithm],
            )
            return decoded
        except jwt.PyJWTError as exc:
            raise AuthenticationError("Token de acceso inválido o expirado.") from exc

    def generate_refresh_token(self) -> tuple[str, str]:
        raw = secrets.token_urlsafe(48)
        return raw, self.hash_refresh_token(raw)

    def hash_refresh_token(self, raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode()).hexdigest()
