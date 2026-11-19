from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError

from sajona_core.application.dto import (
    SyncMutationItem,
    SyncMutationResult,
    SyncPushResponse,
)
from sajona_core.application.ports import CoreRepositoryPort
from sajona_core.application.produccion_service import ProduccionService
from sajona_core.application.rbac import require_permission
from sajona_core.domain.entities import Usuario
from sajona_core.domain.enums import SyncSource
from sajona_core.domain.exceptions import (
    AuthorizationError,
    BusinessRuleViolationError,
    ConflictError,
    DomainError,
)

SYNC_ENTITY_ORDER: list[str] = [
    "variedades",
    "ubicaciones",
    "funcionarios",
    "propagacion",
    "transplante_bolsa",
    "revisiones_bolsa",
    "lotes_planta_madre",
    "unidades_planta_madre",
    "extracciones_madre",
]


class SyncService:
    def __init__(self, repo: CoreRepositoryPort, produccion: ProduccionService) -> None:
        self._repo = repo
        self._produccion = produccion

    async def push(
        self,
        actor: Usuario,
        mutations: list[SyncMutationItem],
        correlation_id: str,
    ) -> SyncPushResponse:
        results: list[SyncMutationResult] = []
        # Procesa estrictamente en el orden recibido (cola causal secuencial del cliente)
        for item in mutations:
            res = await self._process_single(actor, item, correlation_id)
            results.append(res)
        return SyncPushResponse(server_cursor=datetime.now(UTC), results=results)

    async def pull(self, actor: Usuario, since: datetime | None) -> dict[str, Any]:
        changes: dict[str, list[dict[str, Any]]] = {}
        for entity_type in SYNC_ENTITY_ORDER:
            try:
                require_permission(actor.role, entity_type, "read")
            except AuthorizationError:
                continue
            rows = await self._repo.list_entities(
                entity_type, since=since, include_deleted=True
            )
            changes[entity_type] = rows
        return {
            "server_cursor": datetime.now(UTC).isoformat(),
            "changes": changes,
        }

    async def _process_single(
        self, actor: Usuario, item: SyncMutationItem, correlation_id: str
    ) -> SyncMutationResult:
        existing_proc = await self._repo.get_processed_mutation(item.client_mutation_id)
        if existing_proc is not None:
            return SyncMutationResult(
                client_mutation_id=item.client_mutation_id,
                entity_type=item.entity_type,
                entity_id=item.entity_id,
                status="duplicate",
                message="Mutación ya procesada anteriormente (idempotencia).",
                record=existing_proc["result_snapshot"],
            )

        try:
            self._produccion.validate_entity_type(item.entity_type)
            saved = await self._apply_mutation(actor, item, correlation_id)
            await self._repo.save_processed_mutation(
                client_mutation_id=item.client_mutation_id,
                user_id=actor.id,
                entity_type=item.entity_type,
                entity_id=item.entity_id,
                operation=item.operation,
                result_snapshot=saved,
            )
            return SyncMutationResult(
                client_mutation_id=item.client_mutation_id,
                entity_type=item.entity_type,
                entity_id=item.entity_id,
                status="applied",
                record=saved,
            )
        except ConflictError as exc:
            srv = await self._repo.get_entity(
                item.entity_type, item.entity_id, include_deleted=True
            )
            return SyncMutationResult(
                client_mutation_id=item.client_mutation_id,
                entity_type=item.entity_type,
                entity_id=item.entity_id,
                status="conflict",
                message=exc.message,
                server_record=srv,
            )
        except (
            AuthorizationError,
            BusinessRuleViolationError,
            DomainError,
            ValidationError,
        ) as exc:
            msg = exc.message if isinstance(exc, DomainError) else str(exc)
            return SyncMutationResult(
                client_mutation_id=item.client_mutation_id,
                entity_type=item.entity_type,
                entity_id=item.entity_id,
                status="rejected",
                message=msg,
            )

    async def _apply_mutation(
        self, actor: Usuario, item: SyncMutationItem, correlation_id: str
    ) -> dict[str, Any]:
        if item.operation == "DELETE":
            return await self._produccion.delete_record(
                actor,
                item.entity_type,
                item.entity_id,
                expected_version=item.base_version or None,
                correlation_id=correlation_id,
                source=SyncSource.OFFLINE_SYNC,
            )

        payload = dict(item.payload)
        payload["id"] = item.entity_id
        payload["client_mutation_id"] = item.client_mutation_id
        # Deshabilitamos promoción automática en offline sync (cliente encola entidades explícitas)
        if item.entity_type == "transplante_bolsa":
            payload["promover_planta_madre"] = False

        existing = await self._repo.get_entity(
            item.entity_type, item.entity_id, include_deleted=True
        )
        if item.operation == "UPDATE" or existing is not None:
            expected_v = item.base_version if item.base_version > 0 else 1
            return await self._produccion.create_or_update(
                actor,
                item.entity_type,
                payload,
                entity_id=item.entity_id,
                expected_version=expected_v,
                correlation_id=correlation_id,
                source=SyncSource.OFFLINE_SYNC,
            )

        return await self._produccion.create_or_update(
            actor,
            item.entity_type,
            payload,
            correlation_id=correlation_id,
            source=SyncSource.OFFLINE_SYNC,
        )
