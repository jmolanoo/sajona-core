from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, EmailStr, Field

from sajona_core.domain.enums import (
    EstadoLote,
    EstadoPlantaMadre,
    EstadoSanitario,
    FaseBolsa,
    RoleName,
    TipoIncorporacion,
    TipoLoteTransplante,
    TipoPropagacion,
    TipoUbicacion,
)


class LoginRequest(BaseModel):
    identifier: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=4, max_length=128)


class UserProfileDTO(BaseModel):
    id: str
    username: str
    email: EmailStr
    role: RoleName
    full_name: str
    funcionario_id: str | None = None
    is_active: bool = True
    must_change_password: bool = False
    permissions: dict[str, list[str]] = Field(default_factory=dict)


class LoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserProfileDTO


class PasswordResetRequestDTO(BaseModel):
    email: EmailStr


class PasswordResetConfirmDTO(BaseModel):
    token: str = Field(..., min_length=10)
    new_password: str = Field(..., min_length=8, max_length=128)


class AdminUserCreateDTO(BaseModel):
    username: str = Field(..., min_length=3, max_length=60)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: RoleName
    nombre: str = Field(..., min_length=2, max_length=80)
    apellido: str = Field(..., min_length=2, max_length=80)
    documento: str = Field(..., min_length=4, max_length=40)
    telefono: str = Field(default="3000000000", max_length=30)
    cargo: str = Field(default="Operario de Cultivo", max_length=80)


class AdminUserUpdateDTO(BaseModel):
    role: RoleName | None = None
    is_active: bool | None = None
    reset_password: str | None = Field(default=None, min_length=8, max_length=128)


class VariedadPayload(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    nombre: str = Field(..., min_length=2, max_length=100)
    quimiotipo: str = Field(default="Alto CBD", max_length=60)
    dias_vegetativo_est: int = Field(default=21, ge=1, le=365)
    dias_floracion_est: int = Field(default=56, ge=1, le=365)
    descripcion: str = Field(default="", max_length=300)
    activo: bool = True
    version: int = 1
    client_mutation_id: str | None = None


class UbicacionPayload(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    nombre: str = Field(..., min_length=2, max_length=100)
    tipo: TipoUbicacion = TipoUbicacion.INVERNADERO
    capacidad_unidades: int = Field(default=500, ge=1, le=100000)
    activo: bool = True
    version: int = 1
    client_mutation_id: str | None = None


class FuncionarioPayload(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    nombre: str = Field(..., min_length=2, max_length=80)
    apellido: str = Field(..., min_length=2, max_length=80)
    documento: str = Field(..., min_length=4, max_length=40)
    email: EmailStr
    telefono: str = Field(default="", max_length=30)
    cargo: str = Field(default="Operario de Cultivo", max_length=80)
    activo: bool = True
    version: int = 1
    client_mutation_id: str | None = None


class PropagacionPayload(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    codigo_lote: str = Field(..., min_length=2, max_length=64)
    fecha_siembra: date
    variedad_id: str
    ubicacion_id: str | None = None
    responsable_id: str | None = None
    tipo_propagacion: TipoPropagacion = TipoPropagacion.ESQUEJE
    tipo_incorporacion: TipoIncorporacion = TipoIncorporacion.PROPIA
    origen_extraccion_id: str | None = None
    proveedor: str = Field(default="", max_length=150)
    cantidad_material: int = Field(..., gt=0, le=1000000)
    cantidad_plantas_madre: int = Field(default=0, ge=0, le=1000000)
    bajas_propagacion: int = Field(default=0, ge=0, le=1000000)
    estado_lote: EstadoLote = EstadoLote.SIEMBRA
    observaciones: str = Field(default="", max_length=500)
    version: int = 1
    client_mutation_id: str | None = None


class TransplanteBolsaPayload(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    lote_id: str
    codigo_transplante: str = Field(default="", max_length=64)
    fecha_transplante: date
    ubicacion_id: str
    responsable_id: str | None = None
    cama_o_mesa: str = Field(default="Mesa B1", max_length=80)
    cantidad_procesada: int = Field(..., gt=0, le=1000000)
    cantidad_buenas: int = Field(..., ge=0, le=1000000)
    cantidad_malas: int | None = None
    porcentaje_buenas: Decimal | None = None
    porcentaje_malas: Decimal | None = None
    alerta_merma: bool | None = None
    tipo_lote: TipoLoteTransplante = TipoLoteTransplante.PLANTA_COMERCIAL
    capacidad_bolsa: str = Field(default="1L", max_length=40)
    promover_planta_madre: bool = False
    observaciones: str = Field(default="", max_length=500)
    version: int = 1
    client_mutation_id: str | None = None


class RevisionBolsaPayload(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    transplante_id: str
    fecha_revision: date
    fase: FaseBolsa = FaseBolsa.ENRAIZAMIENTO
    unidades_revisadas: int = Field(..., gt=0, le=1000000)
    contador_buenos: int = Field(..., ge=0, le=1000000)
    contador_malos: int = Field(..., ge=0, le=1000000)
    tipo_complicacion: str = Field(default="Ninguna", max_length=100)
    estado_sanitario: EstadoSanitario = EstadoSanitario.OPTIMO
    responsable_id: str | None = None
    observaciones: str = Field(default="", max_length=500)
    version: int = 1
    client_mutation_id: str | None = None


class LotePlantaMadrePayload(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    lote_id: str
    transplante_bolsa_id: str | None = None
    fecha_establecimiento: date
    ubicacion_id: str | None = None
    cantidad_madres_inicial: int = Field(..., gt=0, le=100000)
    cantidad_madres_activas: int | None = None
    observaciones: str = Field(default="", max_length=500)
    version: int = 1
    client_mutation_id: str | None = None


class UnidadPlantaMadrePayload(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    lote_madre_id: str
    numero_planta: int = Field(..., gt=0, le=1000000)
    codigo_planta: str = Field(default="", max_length=64)
    estado_planta: EstadoPlantaMadre = EstadoPlantaMadre.ACTIVA
    total_esquejes: int = Field(default=0, ge=0, le=1000000)
    total_semillas: int = Field(default=0, ge=0, le=1000000)
    ultima_extraccion: date | None = None
    observaciones: str = Field(default="", max_length=500)
    version: int = 1
    client_mutation_id: str | None = None


class DetallePlantaExtraccionItem(BaseModel):
    unidad_id: str | None = None
    numero_planta: int = Field(..., gt=0)
    esquejes: int = Field(default=0, ge=0, le=50000)
    semillas: int = Field(default=0, ge=0, le=50000)


class ExtraccionMadrePayload(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    lote_madre_id: str
    fecha_transplante_ref: date
    fecha_extraccion: date
    responsable_id: str | None = None
    detalle_plantas: list[DetallePlantaExtraccionItem] = Field(..., min_length=1)
    total_esquejes: int | None = None
    total_semillas: int | None = None
    lote_hijo_codigo: str | None = Field(default=None, max_length=64)
    observaciones: str = Field(default="", max_length=500)
    version: int = 1
    client_mutation_id: str | None = None


class SyncMutationItem(BaseModel):
    client_mutation_id: str = Field(..., min_length=8, max_length=128)
    entity_type: str
    entity_id: str
    operation: Literal["CREATE", "UPDATE", "DELETE"]
    base_version: int = 0
    payload: dict[str, Any] = Field(default_factory=dict)


class SyncPushRequest(BaseModel):
    mutations: list[SyncMutationItem] = Field(..., max_length=200)


class SyncMutationResult(BaseModel):
    client_mutation_id: str
    entity_type: str
    entity_id: str
    status: Literal["applied", "duplicate", "conflict", "rejected"]
    message: str = ""
    record: dict[str, Any] | None = None
    server_record: dict[str, Any] | None = None


class SyncPushResponse(BaseModel):
    server_cursor: datetime
    results: list[SyncMutationResult]
