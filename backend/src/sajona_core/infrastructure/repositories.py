from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Date, Numeric, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from sajona_core.domain.entities import Funcionario, Usuario
from sajona_core.domain.enums import RoleName
from sajona_core.domain.exceptions import ConflictError
from sajona_core.infrastructure.mappers import model_to_dict
from sajona_core.infrastructure.models import (
    ExtraccionMadreModel,
    FuncionarioModel,
    LotePlantaMadreModel,
    PasswordResetTokenModel,
    ProcessedMutationModel,
    PropagacionModel,
    RefreshTokenModel,
    RevisionBolsaModel,
    TransplanteBolsaModel,
    UbicacionModel,
    UnidadPlantaMadreModel,
    UsuarioModel,
    VariedadModel,
)

MODEL_MAP: dict[str, type[Any]] = {
    "variedades": VariedadModel,
    "ubicaciones": UbicacionModel,
    "funcionarios": FuncionarioModel,
    "propagacion": PropagacionModel,
    "transplante_bolsa": TransplanteBolsaModel,
    "revisiones_bolsa": RevisionBolsaModel,
    "lotes_planta_madre": LotePlantaMadreModel,
    "unidades_planta_madre": UnidadPlantaMadreModel,
    "extracciones_madre": ExtraccionMadreModel,
}


def _to_user_domain(m: UsuarioModel) -> Usuario:
    return Usuario(
        id=m.id,
        version=m.version,
        created_at=m.created_at,
        updated_at=m.updated_at,
        deleted_at=m.deleted_at,
        username=m.username,
        email=m.email,
        password_hash=m.password_hash,
        role=RoleName(m.role),
        funcionario_id=m.funcionario_id,
        is_active=m.is_active,
        must_change_password=m.must_change_password,
    )


class SqlAlchemyAuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_user_by_identifier(self, identifier: str) -> Usuario | None:
        stmt = select(UsuarioModel).where(
            (UsuarioModel.username == identifier) | (UsuarioModel.email == identifier)
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_user_domain(row) if row else None

    async def get_user_by_id(self, user_id: str) -> Usuario | None:
        row = await self._session.get(UsuarioModel, user_id)
        return _to_user_domain(row) if row else None

    async def list_users(self) -> list[dict[str, Any]]:
        rows = (await self._session.execute(select(UsuarioModel))).scalars().all()
        result: list[dict[str, Any]] = []
        for u in rows:
            d = model_to_dict(u)
            d.pop("password_hash", None)
            result.append(d)
        return result

    async def create_user(self, user: Usuario, funcionario: Funcionario | None = None) -> Usuario:
        if funcionario is not None:
            fm = FuncionarioModel(
                id=funcionario.id,
                nombre=funcionario.nombre,
                apellido=funcionario.apellido,
                documento=funcionario.documento,
                email=funcionario.email,
                telefono=funcionario.telefono,
                cargo=funcionario.cargo,
                activo=funcionario.activo,
            )
            self._session.add(fm)
            await self._session.flush()
        um = UsuarioModel(
            id=user.id,
            username=user.username,
            email=user.email,
            password_hash=user.password_hash,
            role=user.role.value,
            funcionario_id=user.funcionario_id,
            is_active=user.is_active,
            must_change_password=user.must_change_password,
            version=user.version,
        )
        self._session.add(um)
        await self._session.flush()
        return _to_user_domain(um)

    async def update_user(self, user: Usuario) -> Usuario:
        um = await self._session.get(UsuarioModel, user.id)
        if um is None:
            raise ValueError("Usuario inexistente.")
        um.role = user.role.value
        um.is_active = user.is_active
        um.password_hash = user.password_hash
        um.must_change_password = user.must_change_password
        um.version = user.version
        um.updated_at = datetime.now(UTC)
        await self._session.flush()
        return _to_user_domain(um)

    async def store_refresh_token(
        self, token_id: str, user_id: str, token_hash: str, expires_at: datetime
    ) -> None:
        self._session.add(
            RefreshTokenModel(
                id=token_id,
                user_id=user_id,
                token_hash=token_hash,
                expires_at=expires_at,
                revoked=False,
            )
        )
        await self._session.flush()

    async def get_refresh_token(self, token_hash: str) -> dict[str, Any] | None:
        stmt = select(RefreshTokenModel).where(RefreshTokenModel.token_hash == token_hash)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            return None
        return {
            "id": row.id,
            "user_id": row.user_id,
            "expires_at": row.expires_at,
            "revoked": row.revoked,
        }

    async def revoke_refresh_token(self, token_id: str) -> None:
        await self._session.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.id == token_id)
            .values(revoked=True)
        )
        await self._session.flush()

    async def revoke_all_user_refresh_tokens(self, user_id: str) -> None:
        await self._session.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.user_id == user_id)
            .values(revoked=True)
        )
        await self._session.flush()

    async def create_password_reset_token(
        self, reset_id: str, user_id: str, token_hash: str, expires_at: datetime
    ) -> None:
        self._session.add(
            PasswordResetTokenModel(
                id=reset_id,
                user_id=user_id,
                token_hash=token_hash,
                expires_at=expires_at,
                used=False,
            )
        )
        await self._session.flush()

    async def consume_password_reset_token(self, token_hash: str) -> str | None:
        stmt = select(PasswordResetTokenModel).where(
            PasswordResetTokenModel.token_hash == token_hash,
            PasswordResetTokenModel.used.is_(False),
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            return None
        exp = row.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=UTC)
        if exp < datetime.now(UTC):
            return None
        row.used = True
        await self._session.flush()
        return row.user_id


class SqlAlchemyCoreRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_entities(
        self,
        entity_type: str,
        *,
        since: datetime | None = None,
        include_deleted: bool = False,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        model_cls = MODEL_MAP[entity_type]
        stmt = select(model_cls)
        if not include_deleted:
            stmt = stmt.where(model_cls.deleted_at.is_(None))
        if since is not None:
            stmt = stmt.where(model_cls.updated_at >= since)
        if filters:
            for key, val in filters.items():
                if hasattr(model_cls, key):
                    stmt = stmt.where(getattr(model_cls, key) == val)
        stmt = stmt.order_by(model_cls.created_at.desc())
        rows = (await self._session.execute(stmt)).scalars().all()
        return [model_to_dict(r) for r in rows]

    async def get_entity(
        self, entity_type: str, entity_id: str, *, include_deleted: bool = False
    ) -> dict[str, Any] | None:
        model_cls = MODEL_MAP[entity_type]
        row = await self._session.get(model_cls, entity_id)
        if row is None or (not include_deleted and row.deleted_at is not None):
            return None
        return model_to_dict(row)

    async def upsert_entity(
        self, entity_type: str, data: dict[str, Any], *, expected_version: int | None = None
    ) -> dict[str, Any]:
        model_cls = MODEL_MAP[entity_type]
        entity_id = str(data["id"])
        existing = await self._session.get(model_cls, entity_id)
        now = datetime.now(UTC)

        if existing is None:
            clean = self._filter_columns(model_cls, data)
            clean["version"] = int(data.get("version") or 1)
            clean["created_at"] = now
            clean["updated_at"] = now
            clean["deleted_at"] = None
            obj = model_cls(**clean)
            self._session.add(obj)
            await self._session.flush()
            return model_to_dict(obj)

        if expected_version is not None and existing.version != expected_version:
            raise ConflictError(
                f"Versión esperada ({expected_version}) difiere de la versión en servidor "
                f"({existing.version})."
            )

        clean = self._filter_columns(model_cls, data)
        for key, val in clean.items():
            if key not in {"id", "created_at", "version"}:
                setattr(existing, key, val)
        existing.version = existing.version + 1
        existing.updated_at = now
        existing.deleted_at = None
        await self._session.flush()
        return model_to_dict(existing)

    async def soft_delete_entity(
        self, entity_type: str, entity_id: str, *, expected_version: int | None = None
    ) -> dict[str, Any]:
        model_cls = MODEL_MAP[entity_type]
        existing = await self._session.get(model_cls, entity_id)
        if existing is None:
            raise ValueError("Entidad inexistente.")
        if expected_version is not None and existing.version != expected_version:
            raise ConflictError(
                f"Versión esperada ({expected_version}) difiere de servidor ({existing.version})."
            )
        now = datetime.now(UTC)
        existing.deleted_at = now
        existing.updated_at = now
        existing.version = existing.version + 1
        await self._session.flush()
        return model_to_dict(existing)

    async def get_processed_mutation(self, client_mutation_id: str) -> dict[str, Any] | None:
        row = await self._session.get(ProcessedMutationModel, client_mutation_id)
        return model_to_dict(row) if row else None

    async def save_processed_mutation(
        self,
        client_mutation_id: str,
        user_id: str,
        entity_type: str,
        entity_id: str,
        operation: str,
        result_snapshot: dict[str, Any],
    ) -> None:
        self._session.add(
            ProcessedMutationModel(
                client_mutation_id=client_mutation_id,
                user_id=user_id,
                entity_type=entity_type,
                entity_id=entity_id,
                operation=operation,
                result_snapshot=result_snapshot,
            )
        )
        await self._session.flush()

    async def get_lote_traceability(self, lote_id: str) -> dict[str, Any] | None:
        lote = await self.get_entity("propagacion", lote_id)
        if lote is None:
            return None
        transplantes = await self.list_entities("transplante_bolsa", filters={"lote_id": lote_id})
        tp_ids = [str(t["id"]) for t in transplantes]
        all_revs = await self.list_entities("revisiones_bolsa")
        revisiones = [r for r in all_revs if str(r["transplante_id"]) in tp_ids]

        lotes_madre = await self.list_entities("lotes_planta_madre", filters={"lote_id": lote_id})
        lm_ids = [str(m["id"]) for m in lotes_madre]
        all_units = await self.list_entities("unidades_planta_madre")
        unidades = [u for u in all_units if str(u["lote_madre_id"]) in lm_ids]
        all_ext = await self.list_entities("extracciones_madre")
        extracciones = [e for e in all_ext if str(e["lote_madre_id"]) in lm_ids]
        ext_ids = {str(e["id"]) for e in extracciones}
        all_props = await self.list_entities("propagacion")
        hijos = [p for p in all_props if str(p.get("origen_extraccion_id") or "") in ext_ids]

        procesado_bolsa = sum(int(t["cantidad_procesada"]) for t in transplantes)
        buenas_bolsa = sum(int(t["cantidad_buenas"]) for t in transplantes)
        bajas_rev = sum(int(r["contador_malos"]) for r in revisiones)
        saldo_propagacion = max(
            0,
            int(lote["cantidad_material"])
            - int(lote.get("bajas_propagacion", 0))
            - procesado_bolsa,
        )
        return {
            "lote": lote,
            "resumen": {
                "saldo_disponible_propagacion": saldo_propagacion,
                "procesado_bolsa": procesado_bolsa,
                "buenas_bolsa": buenas_bolsa,
                "bajas_en_revisiones": bajas_rev,
                "vivas_en_bolsa": max(0, buenas_bolsa - bajas_rev),
                "unidades_madre": len(unidades),
                "total_esquejes_extraidos": sum(int(e["total_esquejes"]) for e in extracciones),
                "total_semillas_extraidas": sum(int(e["total_semillas"]) for e in extracciones),
                "lotes_hijos_derivados": len(hijos),
            },
            "transplantes_bolsa": transplantes,
            "revisiones_bolsa": revisiones,
            "lotes_planta_madre": lotes_madre,
            "unidades_planta_madre": unidades,
            "extracciones_madre": extracciones,
            "lotes_hijos": hijos,
        }

    def _coerce_column_value(self, col: Any, val: Any) -> Any:
        if val is None:
            return None
        if isinstance(col.type, Date) and isinstance(val, str):
            return date.fromisoformat(val[:10])
        if isinstance(col.type, Numeric) and not isinstance(val, Decimal):
            return Decimal(str(val))
        return val

    def _filter_columns(self, model_cls: type[Any], data: dict[str, Any]) -> dict[str, Any]:
        cols = model_cls.__table__.columns
        return {
            k: self._coerce_column_value(cols[k], v)
            for k, v in data.items()
            if k in cols
        }
