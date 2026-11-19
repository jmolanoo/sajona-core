from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any

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


@dataclass
class SyncMetadata:
    id: str
    version: int = 1
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
    client_mutation_id: str | None = None


@dataclass
class Funcionario(SyncMetadata):
    nombre: str = ""
    apellido: str = ""
    documento: str = ""
    email: str = ""
    telefono: str = ""
    cargo: str = "Operario de Cultivo"
    activo: bool = True


@dataclass
class Usuario(SyncMetadata):
    username: str = ""
    email: str = ""
    password_hash: str = ""
    role: RoleName = RoleName.OPERARIO
    funcionario_id: str | None = None
    is_active: bool = True
    must_change_password: bool = False


@dataclass
class Variedad(SyncMetadata):
    nombre: str = ""
    quimiotipo: str = "Alto CBD"
    dias_vegetativo_est: int = 21
    dias_floracion_est: int = 56
    descripcion: str = ""
    activo: bool = True


@dataclass
class Ubicacion(SyncMetadata):
    nombre: str = ""
    tipo: TipoUbicacion = TipoUbicacion.INVERNADERO
    capacidad_unidades: int = 500
    activo: bool = True


@dataclass
class Propagacion(SyncMetadata):
    codigo_lote: str = ""
    fecha_siembra: date = field(default_factory=date.today)
    variedad_id: str = ""
    ubicacion_id: str | None = None
    responsable_id: str | None = None
    tipo_propagacion: TipoPropagacion = TipoPropagacion.ESQUEJE
    tipo_incorporacion: TipoIncorporacion = TipoIncorporacion.PROPIA
    origen_extraccion_id: str | None = None
    proveedor: str = ""
    cantidad_material: int = 0
    cantidad_plantas_madre: int = 0
    bajas_propagacion: int = 0
    estado_lote: EstadoLote = EstadoLote.SIEMBRA
    observaciones: str = ""


@dataclass
class TransplanteBolsa(SyncMetadata):
    lote_id: str = ""
    codigo_transplante: str = ""
    fecha_transplante: date = field(default_factory=date.today)
    ubicacion_id: str = ""
    responsable_id: str | None = None
    cama_o_mesa: str = ""
    cantidad_procesada: int = 0
    cantidad_buenas: int = 0
    cantidad_malas: int = 0
    porcentaje_buenas: Decimal = Decimal("100.00")
    porcentaje_malas: Decimal = Decimal("0.00")
    alerta_merma: bool = False
    tipo_lote: TipoLoteTransplante = TipoLoteTransplante.PLANTA_COMERCIAL
    capacidad_bolsa: str = "1L"
    observaciones: str = ""


@dataclass
class RevisionBolsa(SyncMetadata):
    transplante_id: str = ""
    fecha_revision: date = field(default_factory=date.today)
    fase: FaseBolsa = FaseBolsa.ENRAIZAMIENTO
    unidades_revisadas: int = 0
    contador_buenos: int = 0
    contador_malos: int = 0
    tipo_complicacion: str = "Ninguna"
    estado_sanitario: EstadoSanitario = EstadoSanitario.OPTIMO
    responsable_id: str | None = None
    observaciones: str = ""


@dataclass
class LotePlantaMadre(SyncMetadata):
    lote_id: str = ""
    transplante_bolsa_id: str | None = None
    fecha_establecimiento: date = field(default_factory=date.today)
    ubicacion_id: str | None = None
    cantidad_madres_inicial: int = 0
    cantidad_madres_activas: int = 0
    observaciones: str = ""


@dataclass
class UnidadPlantaMadre(SyncMetadata):
    lote_madre_id: str = ""
    numero_planta: int = 1
    codigo_planta: str = ""
    estado_planta: EstadoPlantaMadre = EstadoPlantaMadre.ACTIVA
    total_esquejes: int = 0
    total_semillas: int = 0
    ultima_extraccion: date | None = None
    observaciones: str = ""


@dataclass
class ExtraccionMadre(SyncMetadata):
    lote_madre_id: str = ""
    fecha_transplante_ref: date = field(default_factory=date.today)
    fecha_extraccion: date = field(default_factory=date.today)
    responsable_id: str | None = None
    detalle_plantas: list[dict[str, Any]] = field(default_factory=list)
    total_esquejes: int = 0
    total_semillas: int = 0
    lote_hijo_codigo: str | None = None
    observaciones: str = ""


@dataclass
class AuditLogEntry:
    id: str
    correlation_id: str
    user_id: str | None
    username: str
    role: str
    entity_type: str
    entity_id: str
    action: str
    source: str
    result: str
    before_state: dict[str, Any] | None = None
    after_state: dict[str, Any] | None = None
    created_at: datetime | None = None
