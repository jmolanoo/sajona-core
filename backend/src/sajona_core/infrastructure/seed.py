from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
from sajona_core.infrastructure.models import (
    ExtraccionMadreModel,
    FuncionarioModel,
    LotePlantaMadreModel,
    PropagacionModel,
    RevisionBolsaModel,
    TransplanteBolsaModel,
    UbicacionModel,
    UnidadPlantaMadreModel,
    UsuarioModel,
    VariedadModel,
)
from sajona_core.infrastructure.security import Argon2PasswordHasher


async def run_seed_if_empty(session: AsyncSession) -> None:
    existing = (await session.execute(select(UsuarioModel.id).limit(1))).scalar_one_or_none()
    if existing is not None:
        return

    hasher = Argon2PasswordHasher()
    f_admin = FuncionarioModel(
        id="00000000-0000-4000-8000-000000000101",
        nombre="Carlos",
        apellido="Mendoza",
        documento="1075100101",
        email="admin@sajona.co",
        telefono="3115550101",
        cargo="Administrador del Sistema",
    )
    f_jefe = FuncionarioModel(
        id="00000000-0000-4000-8000-000000000102",
        nombre="Laura",
        apellido="Quintero",
        documento="1075100102",
        email="jefe@sajona.co",
        telefono="3115550102",
        cargo="Jefe de Proyecto Agrícola",
    )
    f_oper = FuncionarioModel(
        id="00000000-0000-4000-8000-000000000103",
        nombre="Mateo",
        apellido="Rojas",
        documento="1075100103",
        email="operario@sajona.co",
        telefono="3115550103",
        cargo="Operario de Campo",
    )
    f_cons = FuncionarioModel(
        id="00000000-0000-4000-8000-000000000104",
        nombre="Sofía",
        apellido="Vargas",
        documento="1075100104",
        email="consulta@sajona.co",
        telefono="3115550104",
        cargo="Auditoría y Calidad",
    )
    session.add_all([f_admin, f_jefe, f_oper, f_cons])
    await session.flush()

    usuarios = [
        UsuarioModel(
            id="00000000-0000-4000-8000-000000000201",
            username="admin",
            email="admin@sajona.co",
            password_hash=hasher.hash_password("SajonaAdmin2026!"),
            role=RoleName.ADMIN.value,
            funcionario_id=f_admin.id,
        ),
        UsuarioModel(
            id="00000000-0000-4000-8000-000000000202",
            username="jefe",
            email="jefe@sajona.co",
            password_hash=hasher.hash_password("SajonaJefe2026!"),
            role=RoleName.JEFE_PROYECTO.value,
            funcionario_id=f_jefe.id,
        ),
        UsuarioModel(
            id="00000000-0000-4000-8000-000000000203",
            username="operario",
            email="operario@sajona.co",
            password_hash=hasher.hash_password("SajonaCampo2026!"),
            role=RoleName.OPERARIO.value,
            funcionario_id=f_oper.id,
        ),
        UsuarioModel(
            id="00000000-0000-4000-8000-000000000204",
            username="consulta",
            email="consulta@sajona.co",
            password_hash=hasher.hash_password("SajonaAudit2026!"),
            role=RoleName.CONSULTA.value,
            funcionario_id=f_cons.id,
        ),
    ]
    session.add_all(usuarios)

    var_cw = VariedadModel(
        id="00000000-0000-4000-8000-000000000301",
        nombre="Charlotte's Web",
        quimiotipo="Alto CBD",
        dias_vegetativo_est=21,
        dias_floracion_est=56,
        descripcion="Variedad genética medicinal alto CBD (14–16%).",
    )
    var_can = VariedadModel(
        id="00000000-0000-4000-8000-000000000302",
        nombre="Cannatonic",
        quimiotipo="Balanceado CBD/THC",
        dias_vegetativo_est=24,
        dias_floracion_est=60,
        descripcion="Híbrido medicinal estable para clonación vegetativa.",
    )
    var_cbd = VariedadModel(
        id="00000000-0000-4000-8000-000000000303",
        nombre="CBD Therapy",
        quimiotipo="Ultra Alto CBD",
        dias_vegetativo_est=22,
        dias_floracion_est=54,
        descripcion="Ratio > 20:1 CBD/THC para extractos medicinales.",
    )
    session.add_all([var_cw, var_can, var_cbd])

    ub_cub = UbicacionModel(
        id="00000000-0000-4000-8000-000000000401",
        nombre="Cubículo Propagación A",
        tipo=TipoUbicacion.CUBICULO.value,
        capacidad_unidades=1200,
    )
    ub_cm = UbicacionModel(
        id="00000000-0000-4000-8000-000000000402",
        nombre="Casa Malla Madres 01",
        tipo=TipoUbicacion.CASA_MALLA.value,
        capacidad_unidades=400,
    )
    ub_inv = UbicacionModel(
        id="00000000-0000-4000-8000-000000000403",
        nombre="Invernadero Bolsa Sur",
        tipo=TipoUbicacion.INVERNADERO.value,
        capacidad_unidades=2000,
    )
    session.add_all([ub_cub, ub_cm, ub_inv])
    await session.flush()

    # Lote 30 (CV-09): Propagación -> Bolsa -> Madres #15..18 -> Extracción -> Lote hijo
    lote_30 = PropagacionModel(
        id="00000000-0000-4000-8000-000000000501",
        codigo_lote="LOT-2026-030",
        fecha_siembra=date(2026, 8, 15),
        variedad_id=var_cw.id,
        ubicacion_id=ub_cub.id,
        responsable_id=f_jefe.id,
        tipo_propagacion=TipoPropagacion.ESQUEJE.value,
        tipo_incorporacion=TipoIncorporacion.PROPIA.value,
        proveedor="",
        cantidad_material=100,
        cantidad_plantas_madre=80,
        bajas_propagacion=2,
        estado_lote=EstadoLote.FINALIZADO.value,
        observaciones="Lote fundador para establecimiento de bloque de plantas madre.",
    )
    lote_31 = PropagacionModel(
        id="00000000-0000-4000-8000-000000000502",
        codigo_lote="LOT-2026-031",
        fecha_siembra=date(2026, 9, 10),
        variedad_id=var_can.id,
        ubicacion_id=ub_cub.id,
        responsable_id=f_oper.id,
        tipo_propagacion=TipoPropagacion.SEMILLA.value,
        tipo_incorporacion=TipoIncorporacion.COMPRADA.value,
        proveedor="BioGenética Andina SAS",
        cantidad_material=200,
        cantidad_plantas_madre=0,
        bajas_propagacion=4,
        estado_lote=EstadoLote.EN_TRANSPLANTE.value,
        observaciones="Lote comercial con trasplante parcial a bolsa 1L.",
    )
    lote_32 = PropagacionModel(
        id="00000000-0000-4000-8000-000000000503",
        codigo_lote="LOT-2026-032",
        fecha_siembra=date(2026, 10, 5),
        variedad_id=var_cbd.id,
        ubicacion_id=ub_cub.id,
        responsable_id=f_oper.id,
        tipo_propagacion=TipoPropagacion.IN_VITRO.value,
        tipo_incorporacion=TipoIncorporacion.COMPRADA.value,
        proveedor="TecnoInVitro Huila",
        cantidad_material=150,
        cantidad_plantas_madre=30,
        bajas_propagacion=0,
        estado_lote=EstadoLote.SIEMBRA.value,
        observaciones="Lote en aclimatación inicial listo para paso a bolsa.",
    )
    session.add_all([lote_30, lote_31, lote_32])
    await session.flush()

    tp_30 = TransplanteBolsaModel(
        id="00000000-0000-4000-8000-000000000601",
        lote_id=lote_30.id,
        codigo_transplante="TP-LOT30-01",
        fecha_transplante=date(2026, 9, 2),
        ubicacion_id=ub_cm.id,
        responsable_id=f_jefe.id,
        cama_o_mesa="Mesa Madres M1",
        cantidad_procesada=98,
        cantidad_buenas=90,
        cantidad_malas=8,
        porcentaje_buenas=Decimal("91.84"),
        porcentaje_malas=Decimal("8.16"),
        alerta_merma=False,
        tipo_lote=TipoLoteTransplante.PLANTA_MADRE.value,
        capacidad_bolsa="5L",
        observaciones="Promovido a bloque madre con excelente enraizamiento.",
    )
    tp_31 = TransplanteBolsaModel(
        id="00000000-0000-4000-8000-000000000602",
        lote_id=lote_31.id,
        codigo_transplante="TP-LOT31-01",
        fecha_transplante=date(2026, 9, 28),
        ubicacion_id=ub_inv.id,
        responsable_id=f_oper.id,
        cama_o_mesa="Mesa Bolsa B4",
        cantidad_procesada=120,
        cantidad_buenas=88,
        cantidad_malas=32,
        porcentaje_buenas=Decimal("73.33"),
        porcentaje_malas=Decimal("26.67"),
        alerta_merma=True,
        tipo_lote=TipoLoteTransplante.PLANTA_COMERCIAL.value,
        capacidad_bolsa="1L",
        observaciones="Merma elevada (>20%) por pico de humedad nocturna.",
    )
    session.add_all([tp_30, tp_31])
    await session.flush()

    rev_31 = RevisionBolsaModel(
        id="00000000-0000-4000-8000-000000000651",
        transplante_id=tp_31.id,
        fecha_revision=date(2026, 10, 8),
        fase=FaseBolsa.ENRAIZAMIENTO.value,
        unidades_revisadas=88,
        contador_buenos=84,
        contador_malos=4,
        tipo_complicacion="Marchitamiento leve",
        estado_sanitario=EstadoSanitario.OBSERVACION.value,
        responsable_id=f_oper.id,
        observaciones="Se ajustó riego y ventilación lateral en Mesa B4.",
    )
    session.add(rev_31)
    await session.flush()

    lm_30 = LotePlantaMadreModel(
        id="00000000-0000-4000-8000-000000000701",
        lote_id=lote_30.id,
        transplante_bolsa_id=tp_30.id,
        fecha_establecimiento=date(2026, 9, 2),
        ubicacion_id=ub_cm.id,
        cantidad_madres_inicial=90,
        cantidad_madres_activas=4,
        observaciones="Unidades élite seleccionadas #15 a #18 para trazabilidad CV-09.",
    )
    session.add(lm_30)
    await session.flush()

    u15 = UnidadPlantaMadreModel(
        id="00000000-0000-4000-8000-000000000751",
        lote_madre_id=lm_30.id,
        numero_planta=15,
        codigo_planta="PM-LOT30-015",
        estado_planta=EstadoPlantaMadre.ACTIVA.value,
        total_esquejes=30,
        total_semillas=0,
        ultima_extraccion=date(2026, 10, 12),
    )
    u16 = UnidadPlantaMadreModel(
        id="00000000-0000-4000-8000-000000000752",
        lote_madre_id=lm_30.id,
        numero_planta=16,
        codigo_planta="PM-LOT30-016",
        estado_planta=EstadoPlantaMadre.ACTIVA.value,
        total_esquejes=0,
        total_semillas=20,
        ultima_extraccion=date(2026, 10, 12),
    )
    u17 = UnidadPlantaMadreModel(
        id="00000000-0000-4000-8000-000000000753",
        lote_madre_id=lm_30.id,
        numero_planta=17,
        codigo_planta="PM-LOT30-017",
        estado_planta=EstadoPlantaMadre.ACTIVA.value,
        total_esquejes=7,
        total_semillas=0,
        ultima_extraccion=date(2026, 10, 12),
    )
    u18 = UnidadPlantaMadreModel(
        id="00000000-0000-4000-8000-000000000754",
        lote_madre_id=lm_30.id,
        numero_planta=18,
        codigo_planta="PM-LOT30-018",
        estado_planta=EstadoPlantaMadre.REPOSO.value,
        total_esquejes=0,
        total_semillas=40,
        ultima_extraccion=date(2026, 10, 12),
    )
    session.add_all([u15, u16, u17, u18])
    await session.flush()

    ext_30 = ExtraccionMadreModel(
        id="00000000-0000-4000-8000-000000000801",
        lote_madre_id=lm_30.id,
        fecha_transplante_ref=date(2026, 9, 2),
        fecha_extraccion=date(2026, 10, 12),
        responsable_id=f_jefe.id,
        detalle_plantas=[
            {"unidad_id": u15.id, "numero_planta": 15, "esquejes": 30, "semillas": 0},
            {"unidad_id": u16.id, "numero_planta": 16, "esquejes": 0, "semillas": 20},
            {"unidad_id": u17.id, "numero_planta": 17, "esquejes": 7, "semillas": 0},
            {"unidad_id": u18.id, "numero_planta": 18, "esquejes": 0, "semillas": 40},
        ],
        total_esquejes=37,
        total_semillas=60,
        lote_hijo_codigo="LOT-2026-033",
        observaciones="Extracción validada CV-09 con derivación directa a Propagación.",
    )
    session.add(ext_30)
    await session.flush()

    lote_33_hijo = PropagacionModel(
        id="00000000-0000-4000-8000-000000000504",
        codigo_lote="LOT-2026-033",
        fecha_siembra=date(2026, 10, 12),
        variedad_id=var_cw.id,
        ubicacion_id=ub_cub.id,
        responsable_id=f_jefe.id,
        tipo_propagacion=TipoPropagacion.SEMILLA.value,
        tipo_incorporacion=TipoIncorporacion.PROPIA.value,
        origen_extraccion_id=ext_30.id,
        proveedor="",
        cantidad_material=97,
        cantidad_plantas_madre=0,
        bajas_propagacion=0,
        estado_lote=EstadoLote.SIEMBRA.value,
        observaciones="Lote hijo derivado automáticamente de extracción en LOT-2026-030.",
    )
    session.add(lote_33_hijo)
    await session.commit()
