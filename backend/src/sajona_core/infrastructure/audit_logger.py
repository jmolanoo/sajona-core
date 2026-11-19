import json
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from sajona_core.domain.entities import AuditLogEntry
from sajona_core.infrastructure.mappers import model_to_dict
from sajona_core.infrastructure.models import AuditLogModel


def _json_default(val: Any) -> Any:
    if isinstance(val, datetime | date):
        return val.isoformat()
    if isinstance(val, Decimal):
        return float(val)
    return str(val)


def _sanitize(state: dict[str, Any] | None) -> dict[str, Any] | None:
    if state is None:
        return None
    sanitized = dict(state)
    for secret_key in ("password_hash", "password", "token_hash"):
        sanitized.pop(secret_key, None)
    return sanitized


class DualAuditLogger:
    def __init__(self, session: AsyncSession, log_dir: str) -> None:
        self._session = session
        self._log_path = Path(log_dir) / "audit.jsonl"

    async def log(self, entry: AuditLogEntry) -> None:
        now = entry.created_at or datetime.now(UTC)
        before_clean = _sanitize(entry.before_state)
        after_clean = _sanitize(entry.after_state)

        record = AuditLogModel(
            id=entry.id,
            correlation_id=entry.correlation_id,
            user_id=entry.user_id,
            username=entry.username,
            role=entry.role,
            entity_type=entry.entity_type,
            entity_id=entry.entity_id,
            action=entry.action,
            source=entry.source,
            result=entry.result,
            before_state=before_clean,
            after_state=after_clean,
            created_at=now,
        )
        self._session.add(record)
        await self._session.flush()

        try:
            self._log_path.parent.mkdir(parents=True, exist_ok=True)
            line = json.dumps(
                {
                    "id": entry.id,
                    "timestamp": now.isoformat(),
                    "correlation_id": entry.correlation_id,
                    "user_id": entry.user_id,
                    "username": entry.username,
                    "role": entry.role,
                    "entity_type": entry.entity_type,
                    "entity_id": entry.entity_id,
                    "action": entry.action,
                    "source": entry.source,
                    "result": entry.result,
                },
                default=_json_default,
            )
            with self._log_path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except OSError:
            pass

    async def list_recent(self, limit: int = 100) -> list[dict[str, Any]]:
        stmt = select(AuditLogModel).order_by(desc(AuditLogModel.created_at)).limit(limit)
        res = await self._session.execute(stmt)
        return [model_to_dict(row) for row in res.scalars().all()]
