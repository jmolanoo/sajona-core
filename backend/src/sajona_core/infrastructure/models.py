from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class SyncColsMixin:
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    client_mutation_id: Mapped[str | None] = mapped_column(String(128), nullable=True)


class FuncionarioModel(Base, SyncColsMixin):
    __tablename__ = "funcionarios"

    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    apellido: Mapped[str] = mapped_column(String(80), nullable=False)
    documento: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    telefono: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    cargo: Mapped[str] = mapped_column(String(80), nullable=False, default="Operario de Cultivo")
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class UsuarioModel(Base, SyncColsMixin):
    __tablename__ = "usuarios"

    username: Mapped[str] = mapped_column(String(60), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    funcionario_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("funcionarios.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class RefreshTokenModel(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("usuarios.id"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )


class PasswordResetTokenModel(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("usuarios.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class VariedadModel(Base, SyncColsMixin):
    __tablename__ = "variedades"

    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    quimiotipo: Mapped[str] = mapped_column(String(60), nullable=False, default="Alto CBD")
    dias_vegetativo_est: Mapped[int] = mapped_column(Integer, nullable=False, default=21)
    dias_floracion_est: Mapped[int] = mapped_column(Integer, nullable=False, default=56)
    descripcion: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class UbicacionModel(Base, SyncColsMixin):
    __tablename__ = "ubicaciones"

    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    tipo: Mapped[str] = mapped_column(String(32), nullable=False)
    capacidad_unidades: Mapped[int] = mapped_column(Integer, nullable=False, default=500)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class PropagacionModel(Base, SyncColsMixin):
    __tablename__ = "propagaciones"

    codigo_lote: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    fecha_siembra: Mapped[date] = mapped_column(Date, nullable=False)
    variedad_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("variedades.id"), nullable=False
    )
    ubicacion_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("ubicaciones.id"), nullable=True
    )
    responsable_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("funcionarios.id"), nullable=True
    )
    tipo_propagacion: Mapped[str] = mapped_column(String(24), nullable=False)
    tipo_incorporacion: Mapped[str] = mapped_column(String(24), nullable=False)
    origen_extraccion_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    proveedor: Mapped[str] = mapped_column(String(150), nullable=False, default="")
    cantidad_material: Mapped[int] = mapped_column(Integer, nullable=False)
    cantidad_plantas_madre: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    bajas_propagacion: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estado_lote: Mapped[str] = mapped_column(String(24), nullable=False, default="SIEMBRA")
    observaciones: Mapped[str] = mapped_column(Text, nullable=False, default="")


class TransplanteBolsaModel(Base, SyncColsMixin):
    __tablename__ = "transplantes_bolsa"

    lote_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("propagaciones.id"), nullable=False, index=True
    )
    codigo_transplante: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    fecha_transplante: Mapped[date] = mapped_column(Date, nullable=False)
    ubicacion_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ubicaciones.id"), nullable=False
    )
    responsable_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("funcionarios.id"), nullable=True
    )
    cama_o_mesa: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    cantidad_procesada: Mapped[int] = mapped_column(Integer, nullable=False)
    cantidad_buenas: Mapped[int] = mapped_column(Integer, nullable=False)
    cantidad_malas: Mapped[int] = mapped_column(Integer, nullable=False)
    porcentaje_buenas: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    porcentaje_malas: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    alerta_merma: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tipo_lote: Mapped[str] = mapped_column(String(24), nullable=False)
    capacidad_bolsa: Mapped[str] = mapped_column(String(40), nullable=False, default="1L")
    observaciones: Mapped[str] = mapped_column(Text, nullable=False, default="")


class RevisionBolsaModel(Base, SyncColsMixin):
    __tablename__ = "revisiones_bolsa"

    transplante_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("transplantes_bolsa.id"), nullable=False, index=True
    )
    fecha_revision: Mapped[date] = mapped_column(Date, nullable=False)
    fase: Mapped[str] = mapped_column(String(32), nullable=False)
    unidades_revisadas: Mapped[int] = mapped_column(Integer, nullable=False)
    contador_buenos: Mapped[int] = mapped_column(Integer, nullable=False)
    contador_malos: Mapped[int] = mapped_column(Integer, nullable=False)
    tipo_complicacion: Mapped[str] = mapped_column(String(100), nullable=False, default="Ninguna")
    estado_sanitario: Mapped[str] = mapped_column(String(24), nullable=False, default="OPTIMO")
    responsable_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("funcionarios.id"), nullable=True
    )
    observaciones: Mapped[str] = mapped_column(Text, nullable=False, default="")


class LotePlantaMadreModel(Base, SyncColsMixin):
    __tablename__ = "lotes_planta_madre"

    lote_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("propagaciones.id"), nullable=False, index=True
    )
    transplante_bolsa_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("transplantes_bolsa.id"), nullable=True
    )
    fecha_establecimiento: Mapped[date] = mapped_column(Date, nullable=False)
    ubicacion_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("ubicaciones.id"), nullable=True
    )
    cantidad_madres_inicial: Mapped[int] = mapped_column(Integer, nullable=False)
    cantidad_madres_activas: Mapped[int] = mapped_column(Integer, nullable=False)
    observaciones: Mapped[str] = mapped_column(Text, nullable=False, default="")


class UnidadPlantaMadreModel(Base, SyncColsMixin):
    __tablename__ = "unidades_planta_madre"
    __table_args__ = (
        UniqueConstraint("lote_madre_id", "numero_planta", name="uq_lote_madre_num"),
    )

    lote_madre_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("lotes_planta_madre.id"), nullable=False, index=True
    )
    numero_planta: Mapped[int] = mapped_column(Integer, nullable=False)
    codigo_planta: Mapped[str] = mapped_column(String(64), nullable=False)
    estado_planta: Mapped[str] = mapped_column(String(24), nullable=False, default="ACTIVA")
    total_esquejes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_semillas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ultima_extraccion: Mapped[date | None] = mapped_column(Date, nullable=True)
    observaciones: Mapped[str] = mapped_column(Text, nullable=False, default="")


class ExtraccionMadreModel(Base, SyncColsMixin):
    __tablename__ = "extracciones_madre"

    lote_madre_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("lotes_planta_madre.id"), nullable=False, index=True
    )
    fecha_transplante_ref: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_extraccion: Mapped[date] = mapped_column(Date, nullable=False)
    responsable_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("funcionarios.id"), nullable=True
    )
    detalle_plantas: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    total_esquejes: Mapped[int] = mapped_column(Integer, nullable=False)
    total_semillas: Mapped[int] = mapped_column(Integer, nullable=False)
    lote_hijo_codigo: Mapped[str | None] = mapped_column(String(64), nullable=True)
    observaciones: Mapped[str] = mapped_column(Text, nullable=False, default="")


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    username: Mapped[str] = mapped_column(String(60), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(48), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(24), nullable=False)
    source: Mapped[str] = mapped_column(String(24), nullable=False)
    result: Mapped[str] = mapped_column(String(24), nullable=False)
    before_state: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    after_state: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, index=True
    )


class ProcessedMutationModel(Base):
    __tablename__ = "processed_mutations"

    client_mutation_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(48), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    operation: Mapped[str] = mapped_column(String(16), nullable=False)
    result_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
