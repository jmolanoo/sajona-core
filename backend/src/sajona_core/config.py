from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "SAJONA Core API"
    app_version: str = "1.0.0"
    environment: str = "production"
    database_url: str = "postgresql+asyncpg://sajona_core:sajona_core@sajona-core-db:5432/sajona_core"
    jwt_secret_key: str = "dev-secret-key-change-in-production-32chars"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    cookie_secure: bool = False
    audit_log_dir: str = "/tmp/sajona_core_audit"
    seed_demo_data: bool = True
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:8089"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
