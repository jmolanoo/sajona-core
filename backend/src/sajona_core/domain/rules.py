from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from sajona_core.domain.enums import EstadoLote, TipoIncorporacion
from sajona_core.domain.exceptions import BusinessRuleViolationError

UMBRAL_ALERTA_MERMA_PCT = Decimal("20.00")


@dataclass(frozen=True)
class ResultadoSupervivenciaBolsa:
    cantidad_procesada: int
    cantidad_buenas: int
    cantidad_malas: int
    porcentaje_buenas: Decimal
    porcentaje_malas: Decimal
    alerta_merma: bool
    nuevo_saldo_lote: int
    nuevo_estado_lote: EstadoLote


@dataclass(frozen=True)
class TotalesExtraccionMadre:
    total_esquejes: int
    total_semillas: int
    total_general: int


def calcular_saldo_propagacion(
    cantidad_material: int,
    bajas_propagacion: int,
    procesado_en_bolsa: int,
) -> int:
    if cantidad_material <= 0:
        raise BusinessRuleViolationError("La cantidad de material sembrado debe ser mayor a cero.")
    if bajas_propagacion < 0 or bajas_propagacion >= cantidad_material:
        raise BusinessRuleViolationError(
            "Las bajas en propagación deben ser >= 0 y menores al total sembrado."
        )
    if procesado_en_bolsa < 0:
        raise BusinessRuleViolationError("Las unidades trasplantadas no pueden ser negativas.")
    saldo = cantidad_material - bajas_propagacion - procesado_en_bolsa
    if saldo < 0:
        raise BusinessRuleViolationError(
            "El total procesado más las bajas supera la cantidad sembrada en el lote."
        )
    return saldo


def validar_propagacion(
    cantidad_material: int,
    cantidad_plantas_madre: int,
    bajas_propagacion: int,
    tipo_incorporacion: TipoIncorporacion,
    proveedor: str,
    procesado_en_bolsa: int = 0,
) -> EstadoLote:
    saldo = calcular_saldo_propagacion(cantidad_material, bajas_propagacion, procesado_en_bolsa)
    if cantidad_plantas_madre < 0 or cantidad_plantas_madre > cantidad_material:
        raise BusinessRuleViolationError(
            "Las plantas madre estimadas no pueden superar la cantidad sembrada."
        )
    if tipo_incorporacion == TipoIncorporacion.COMPRADA and not proveedor.strip():
        raise BusinessRuleViolationError(
            "Cuando la incorporación es COMPRADA se debe registrar el proveedor o vivero origen."
        )
    if saldo == 0:
        return EstadoLote.FINALIZADO
    if procesado_en_bolsa > 0:
        return EstadoLote.EN_TRANSPLANTE
    return EstadoLote.SIEMBRA


def calcular_transplante_bolsa(
    saldo_disponible: int,
    cantidad_procesada: int,
    cantidad_buenas: int,
    fecha_siembra: date,
    fecha_transplante: date,
) -> ResultadoSupervivenciaBolsa:
    if fecha_transplante < fecha_siembra:
        raise BusinessRuleViolationError(
            "La fecha de trasplante a bolsa no puede ser anterior a la siembra del lote."
        )
    if cantidad_procesada <= 0:
        raise BusinessRuleViolationError(
            "La cantidad procesada hacia bolsa debe ser mayor a cero."
        )
    if cantidad_procesada > saldo_disponible:
        raise BusinessRuleViolationError(
            f"Saldo insuficiente en el lote ({saldo_disponible} disponibles vs "
            f"{cantidad_procesada} solicitadas)."
        )
    if cantidad_buenas < 0 or cantidad_buenas > cantidad_procesada:
        raise BusinessRuleViolationError(
            "La cantidad de plantas buenas debe estar entre 0 y la cantidad procesada."
        )

    cantidad_malas = cantidad_procesada - cantidad_buenas
    pct_buenas = (
        Decimal(cantidad_buenas) * Decimal("100.00") / Decimal(cantidad_procesada)
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    pct_malas = Decimal("100.00") - pct_buenas
    alerta = pct_malas > UMBRAL_ALERTA_MERMA_PCT
    nuevo_saldo = saldo_disponible - cantidad_procesada
    nuevo_estado = EstadoLote.FINALIZADO if nuevo_saldo == 0 else EstadoLote.EN_TRANSPLANTE

    return ResultadoSupervivenciaBolsa(
        cantidad_procesada=cantidad_procesada,
        cantidad_buenas=cantidad_buenas,
        cantidad_malas=cantidad_malas,
        porcentaje_buenas=pct_buenas,
        porcentaje_malas=pct_malas,
        alerta_merma=alerta,
        nuevo_saldo_lote=nuevo_saldo,
        nuevo_estado_lote=nuevo_estado,
    )


def validar_revision_bolsa(
    fecha_transplante: date,
    fecha_revision: date,
    unidades_revisadas: int,
    contador_buenos: int,
    contador_malos: int,
    buenas_totales_transplante: int,
    malos_acumulados_previos: int,
) -> int:
    if fecha_revision < fecha_transplante:
        raise BusinessRuleViolationError(
            "La fecha de revisión no puede ser anterior a la fecha del trasplante."
        )
    if unidades_revisadas <= 0:
        raise BusinessRuleViolationError("Las unidades revisadas deben ser mayores a cero.")
    if contador_buenos < 0 or contador_malos < 0:
        raise BusinessRuleViolationError(
            "Los contadores de buenos y malos no pueden ser negativos."
        )
    if contador_buenos + contador_malos != unidades_revisadas:
        raise BusinessRuleViolationError(
            "La suma de buenos y malos debe coincidir exactamente con las unidades revisadas."
        )
    malos_totales = malos_acumulados_previos + contador_malos
    if malos_totales > buenas_totales_transplante:
        raise BusinessRuleViolationError(
            "Las bajas acumuladas en revisiones superan las plantas buenas trasplantadas."
        )
    return buenas_totales_transplante - malos_totales


def validar_extraccion_madre(
    fecha_transplante_ref: date,
    fecha_extraccion: date,
    detalle_plantas: list[dict[str, Any]],
) -> TotalesExtraccionMadre:
    if fecha_extraccion < fecha_transplante_ref:
        raise BusinessRuleViolationError(
            "La fecha de extracción no puede ser anterior a la fecha de establecimiento."
        )
    if not detalle_plantas:
        raise BusinessRuleViolationError(
            "Debe incluir al menos una planta madre en el detalle de extracción."
        )

    total_esquejes = 0
    total_semillas = 0
    numeros_vistos: set[int] = set()
    for fila in detalle_plantas:
        num = int(fila.get("numero_planta", 0))
        esq = int(fila.get("esquejes", 0))
        sem = int(fila.get("semillas", 0))
        if num <= 0:
            raise BusinessRuleViolationError("El número de planta madre debe ser mayor a cero.")
        if num in numeros_vistos:
            raise BusinessRuleViolationError(f"Planta madre #{num} duplicada en la matriz.")
        numeros_vistos.add(num)
        if esq < 0 or sem < 0:
            raise BusinessRuleViolationError(
                "Las cantidades de esquejes y semillas no pueden ser negativas."
            )
        total_esquejes += esq
        total_semillas += sem

    total_general = total_esquejes + total_semillas
    if total_general <= 0:
        raise BusinessRuleViolationError(
            "La extracción debe producir al menos 1 esqueje o 1 semilla."
        )
    return TotalesExtraccionMadre(
        total_esquejes=total_esquejes,
        total_semillas=total_semillas,
        total_general=total_general,
    )
