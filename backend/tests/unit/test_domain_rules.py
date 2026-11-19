from datetime import date
from decimal import Decimal

import pytest

from sajona_core.domain.enums import EstadoLote, TipoIncorporacion
from sajona_core.domain.exceptions import BusinessRuleViolationError
from sajona_core.domain.rules import (
    calcular_saldo_propagacion,
    calcular_transplante_bolsa,
    validar_extraccion_madre,
    validar_propagacion,
    validar_revision_bolsa,
)


def test_rn01_saldo_y_estado_propagacion() -> None:
    assert calcular_saldo_propagacion(100, 2, 40) == 58
    assert (
        validar_propagacion(
            100, 50, 2, TipoIncorporacion.PROPIA, "", procesado_en_bolsa=0
        )
        == EstadoLote.SIEMBRA
    )
    assert (
        validar_propagacion(
            100, 50, 2, TipoIncorporacion.PROPIA, "", procesado_en_bolsa=40
        )
        == EstadoLote.EN_TRANSPLANTE
    )
    assert (
        validar_propagacion(
            100, 50, 2, TipoIncorporacion.PROPIA, "", procesado_en_bolsa=98
        )
        == EstadoLote.FINALIZADO
    )


def test_rn01_propagacion_validaciones_borde() -> None:
    with pytest.raises(BusinessRuleViolationError):
        calcular_saldo_propagacion(0, 0, 0)
    with pytest.raises(BusinessRuleViolationError):
        calcular_saldo_propagacion(100, 0, -1)
    with pytest.raises(BusinessRuleViolationError):
        calcular_saldo_propagacion(100, 100, 0)
    with pytest.raises(BusinessRuleViolationError):
        calcular_saldo_propagacion(100, 10, 95)
    with pytest.raises(BusinessRuleViolationError):
        validar_propagacion(50, 60, 0, TipoIncorporacion.PROPIA, "")
    with pytest.raises(BusinessRuleViolationError):
        validar_propagacion(100, 0, 0, TipoIncorporacion.COMPRADA, "   ")


def test_rn02_transplante_bolsa_calcula_supervivencia_y_alerta_merma() -> None:
    res_ok = calcular_transplante_bolsa(
        saldo_disponible=100,
        cantidad_procesada=100,
        cantidad_buenas=80,
        fecha_siembra=date(2026, 9, 1),
        fecha_transplante=date(2026, 9, 20),
    )
    assert res_ok.cantidad_malas == 20
    assert res_ok.porcentaje_buenas == Decimal("80.00")
    assert res_ok.porcentaje_malas == Decimal("20.00")
    assert res_ok.alerta_merma is False
    assert res_ok.nuevo_estado_lote == EstadoLote.FINALIZADO

    res_alerta = calcular_transplante_bolsa(
        saldo_disponible=100,
        cantidad_procesada=50,
        cantidad_buenas=35,
        fecha_siembra=date(2026, 9, 1),
        fecha_transplante=date(2026, 9, 20),
    )
    assert res_alerta.porcentaje_malas == Decimal("30.00")
    assert res_alerta.alerta_merma is True
    assert res_alerta.nuevo_saldo_lote == 50
    assert res_alerta.nuevo_estado_lote == EstadoLote.EN_TRANSPLANTE


def test_rn02_transplante_bolsa_rechaza_saldo_cero_o_fechas_invalidas() -> None:
    with pytest.raises(BusinessRuleViolationError):
        calcular_transplante_bolsa(30, 0, 0, date(2026, 9, 10), date(2026, 9, 20))
    with pytest.raises(BusinessRuleViolationError):
        calcular_transplante_bolsa(30, 35, 30, date(2026, 9, 10), date(2026, 9, 20))
    with pytest.raises(BusinessRuleViolationError):
        calcular_transplante_bolsa(50, 20, 21, date(2026, 9, 10), date(2026, 9, 20))
    with pytest.raises(BusinessRuleViolationError):
        calcular_transplante_bolsa(50, 20, 18, date(2026, 9, 10), date(2026, 9, 5))


def test_rn04_revision_periodica_cv05_conserva_vivas_y_rechaza_bordes() -> None:
    vivas = validar_revision_bolsa(
        fecha_transplante=date(2026, 9, 20),
        fecha_revision=date(2026, 9, 30),
        unidades_revisadas=50,
        contador_buenos=46,
        contador_malos=4,
        buenas_totales_transplante=80,
        malos_acumulados_previos=10,
    )
    assert vivas == 66

    with pytest.raises(BusinessRuleViolationError):
        validar_revision_bolsa(date(2026, 9, 20), date(2026, 9, 19), 10, 10, 0, 80, 0)
    with pytest.raises(BusinessRuleViolationError):
        validar_revision_bolsa(date(2026, 9, 20), date(2026, 9, 30), 0, 0, 0, 80, 0)
    with pytest.raises(BusinessRuleViolationError):
        validar_revision_bolsa(date(2026, 9, 20), date(2026, 9, 30), 10, -1, 11, 80, 0)
    with pytest.raises(BusinessRuleViolationError):
        validar_revision_bolsa(date(2026, 9, 20), date(2026, 9, 30), 50, 40, 5, 80, 0)
    with pytest.raises(BusinessRuleViolationError):
        validar_revision_bolsa(date(2026, 9, 20), date(2026, 9, 30), 20, 0, 20, 50, 35)


def test_rn05_extraccion_madre_cv09_exacta_y_bordes() -> None:
    tot = validar_extraccion_madre(
        fecha_transplante_ref=date(2026, 9, 2),
        fecha_extraccion=date(2026, 10, 12),
        detalle_plantas=[
            {"numero_planta": 15, "esquejes": 30, "semillas": 0},
            {"numero_planta": 16, "esquejes": 0, "semillas": 20},
            {"numero_planta": 17, "esquejes": 7, "semillas": 0},
            {"numero_planta": 18, "esquejes": 0, "semillas": 40},
        ],
    )
    assert tot.total_esquejes == 37
    assert tot.total_semillas == 60
    assert tot.total_general == 97

    with pytest.raises(BusinessRuleViolationError):
        validar_extraccion_madre(date(2026, 9, 20), date(2026, 9, 10), [])
    with pytest.raises(BusinessRuleViolationError):
        validar_extraccion_madre(date(2026, 9, 2), date(2026, 10, 12), [])
    with pytest.raises(BusinessRuleViolationError):
        validar_extraccion_madre(
            date(2026, 9, 2),
            date(2026, 10, 12),
            [{"numero_planta": 0, "esquejes": 2, "semillas": 0}],
        )
    with pytest.raises(BusinessRuleViolationError):
        validar_extraccion_madre(
            date(2026, 9, 2),
            date(2026, 10, 12),
            [
                {"numero_planta": 15, "esquejes": 5, "semillas": 0},
                {"numero_planta": 15, "esquejes": 3, "semillas": 0},
            ],
        )
    with pytest.raises(BusinessRuleViolationError):
        validar_extraccion_madre(
            date(2026, 9, 2),
            date(2026, 10, 12),
            [{"numero_planta": 15, "esquejes": -1, "semillas": 3}],
        )
    with pytest.raises(BusinessRuleViolationError):
        validar_extraccion_madre(
            date(2026, 9, 2),
            date(2026, 10, 12),
            [{"numero_planta": 15, "esquejes": 0, "semillas": 0}],
        )
