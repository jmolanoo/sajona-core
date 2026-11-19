from enum import StrEnum


class RoleName(StrEnum):
    ADMIN = "ADMIN"
    JEFE_PROYECTO = "JEFE_PROYECTO"
    OPERARIO = "OPERARIO"
    CONSULTA = "CONSULTA"


class TipoPropagacion(StrEnum):
    ESQUEJE = "ESQUEJE"
    SEMILLA = "SEMILLA"
    IN_VITRO = "IN_VITRO"


class TipoIncorporacion(StrEnum):
    PROPIA = "PROPIA"
    COMPRADA = "COMPRADA"


class EstadoLote(StrEnum):
    SIEMBRA = "SIEMBRA"
    EN_TRANSPLANTE = "EN_TRANSPLANTE"
    FINALIZADO = "FINALIZADO"


class TipoLoteTransplante(StrEnum):
    PLANTA_MADRE = "PLANTA_MADRE"
    PLANTA_COMERCIAL = "PLANTA_COMERCIAL"


class EstadoPlantaMadre(StrEnum):
    ACTIVA = "ACTIVA"
    REPOSO = "REPOSO"
    DESCARTADA = "DESCARTADA"


class FaseBolsa(StrEnum):
    ENRAIZAMIENTO = "ENRAIZAMIENTO"
    BOLSA_INICIAL = "BOLSA_INICIAL"
    ACLIMATACION = "ACLIMATACION"


class EstadoSanitario(StrEnum):
    OPTIMO = "OPTIMO"
    OBSERVACION = "OBSERVACION"
    CRITICO = "CRITICO"


class TipoUbicacion(StrEnum):
    INVERNADERO = "INVERNADERO"
    CASA_MALLA = "CASA_MALLA"
    CUBICULO = "CUBICULO"
    ENRAIZAMIENTO = "ENRAIZAMIENTO"
    CAMPO_BASE = "CAMPO_BASE"


class SyncSource(StrEnum):
    ONLINE = "online"
    OFFLINE_SYNC = "offline_sync"
