from datetime import date
from typing import Any
from uuid import uuid4

from pydantic import BaseModel

from sajona_core.application.dto import (
    ExtraccionMadrePayload,
    FuncionarioPayload,
    LotePlantaMadrePayload,
    PropagacionPayload,
    RevisionBolsaPayload,
    TransplanteBolsaPayload,
    UbicacionPayload,
    UnidadPlantaMadrePayload,
    VariedadPayload,
)
from sajona_core.application.ports import AuditLoggerPort, CoreRepositoryPort
from sajona_core.application.rbac import require_permission
from sajona_core.domain.entities import AuditLogEntry, Usuario
from sajona_core.domain.enums import (
    EstadoLote,
    EstadoPlantaMadre,
    SyncSource,
    TipoIncorporacion,
    TipoLoteTransplante,
    TipoPropagacion,
)
from sajona_core.domain.exceptions import BusinessRuleViolationError, EntityNotFoundError
from sajona_core.domain.rules import (
    calcular_saldo_propagacion,
    calcular_transplante_bolsa,
    validar_extraccion_madre,
    validar_propagacion,
    validar_revision_bolsa,
)

PAYLOAD_SCHEMAS: dict[str, type[BaseModel]] = {
    "variedades": VariedadPayload,
    "ubicaciones": UbicacionPayload,
    "funcionarios": FuncionarioPayload,
    "propagacion": PropagacionPayload,
    "transplante_bolsa": TransplanteBolsaPayload,
    "revisiones_bolsa": RevisionBolsaPayload,
    "lotes_planta_madre": LotePlantaMadrePayload,
    "unidades_planta_madre": UnidadPlantaMadrePayload,
    "extracciones_madre": ExtraccionMadrePayload,
}


def _to_date(val: Any) -> date:
    if isinstance(val, date):
        return val
    return date.fromisoformat(str(val)[:10])


class ProduccionService:
    def __init__(self, repo: CoreRepositoryPort, audit: AuditLoggerPort) -> None:
        self._repo = repo
        self._audit = audit

    def validate_entity_type(self, entity_type: str) -> None:
        if entity_type not in PAYLOAD_SCHEMAS:
            raise EntityNotFoundError("Tipo de entidad", entity_type)

    async def list_records(
        self,
        actor: Usuario,
        entity_type: str,
        *,
        lote_id: str | None = None,
        transplante_id: str | None = None,
        lote_madre_id: str | None = None,
    ) -> list[dict[str, Any]]:
        self.validate_entity_type(entity_type)
        require_permission(actor.role, entity_type, "read")
        filters: dict[str, Any] = {}
        if lote_id:
            filters["lote_id"] = lote_id
        if transplante_id:
            filters["transplante_id"] = transplante_id
        if lote_madre_id:
            filters["lote_madre_id"] = lote_madre_id
        return await self._repo.list_entities(entity_type, filters=filters)

    async def create_or_update(
        self,
        actor: Usuario,
        entity_type: str,
        raw_payload: dict[str, Any],
        *,
        entity_id: str | None = None,
        expected_version: int | None = None,
        correlation_id: str = "",
        source: SyncSource = SyncSource.ONLINE,
    ) -> dict[str, Any]:
        self.validate_entity_type(entity_type)
        is_update = entity_id is not None
        require_permission(actor.role, entity_type, "write")
        payload_data = dict(raw_payload)
        if entity_id:
            payload_data["id"] = entity_id
        model_cls = PAYLOAD_SCHEMAS[entity_type]
        validated = model_cls.model_validate(payload_data)
        data = validated.model_dump(mode="python")

        before = await self._repo.get_entity(entity_type, data["id"]) if is_update else None
        if is_update and before is None:
            raise EntityNotFoundError(entity_type, data["id"])

        clean_data, side_effects = await self._apply_business_rules(entity_type, data)
        if "responsable_id" in clean_data and not clean_data["responsable_id"]:
            clean_data["responsable_id"] = actor.funcionario_id

        saved = await self._repo.upsert_entity(
            entity_type, clean_data, expected_version=expected_version
        )
        await self._execute_side_effects(
            entity_type, saved, side_effects, actor, correlation_id, source
        )
        await self._audit.log(
            AuditLogEntry(
                id=str(uuid4()),
                correlation_id=correlation_id,
                user_id=actor.id,
                username=actor.username,
                role=actor.role.value,
                entity_type=entity_type,
                entity_id=str(saved["id"]),
                action="UPDATE" if before else "CREATE",
                source=source.value,
                result="SUCCESS",
                before_state=before,
                after_state=saved,
            )
        )
        return saved

    async def delete_record(
        self,
        actor: Usuario,
        entity_type: str,
        entity_id: str,
        *,
        expected_version: int | None = None,
        correlation_id: str = "",
        source: SyncSource = SyncSource.ONLINE,
    ) -> dict[str, Any]:
        self.validate_entity_type(entity_type)
        require_permission(actor.role, entity_type, "delete")
        before = await self._repo.get_entity(entity_type, entity_id)
        if before is None:
            raise EntityNotFoundError(entity_type, entity_id)

        deleted = await self._repo.soft_delete_entity(
            entity_type, entity_id, expected_version=expected_version
        )
        await self._recalculate_after_delete(entity_type, before)
        await self._audit.log(
            AuditLogEntry(
                id=str(uuid4()),
                correlation_id=correlation_id,
                user_id=actor.id,
                username=actor.username,
                role=actor.role.value,
                entity_type=entity_type,
                entity_id=entity_id,
                action="DELETE",
                source=source.value,
                result="SUCCESS",
                before_state=before,
                after_state=deleted,
            )
        )
        return deleted

    async def get_traceability(self, actor: Usuario, lote_id: str) -> dict[str, Any]:
        require_permission(actor.role, "propagacion", "read")
        trace = await self._repo.get_lote_traceability(lote_id)
        if trace is None:
            raise EntityNotFoundError("Lote de propagación", lote_id)
        return trace

    async def get_dashboard_summary(
        self,
        actor: Usuario,
        *,
        fecha_inicio: date | None = None,
        fecha_fin: date | None = None,
        variedad_id: str | None = None,
        tipo_propagacion: str | None = None,
    ) -> dict[str, Any]:
        require_permission(actor.role, "propagacion", "read")
        propagaciones = await self._repo.list_entities("propagacion")
        transplantes = await self._repo.list_entities("transplante_bolsa")
        revisiones = await self._repo.list_entities("revisiones_bolsa")
        lotes_madre = await self._repo.list_entities("lotes_planta_madre")
        unidades_madre = await self._repo.list_entities("unidades_planta_madre")
        extracciones = await self._repo.list_entities("extracciones_madre")
        variedades = await self._repo.list_entities("variedades")

        var_map = {str(v["id"]): str(v["nombre"]) for v in variedades}
        filtered_props = self._filter_propagaciones(
            propagaciones, fecha_inicio, fecha_fin, variedad_id, tipo_propagacion
        )
        lote_ids = {str(p["id"]) for p in filtered_props}
        f_trans = [t for t in transplantes if str(t["lote_id"]) in lote_ids]
        trans_ids = {str(t["id"]) for t in f_trans}
        f_revs = [r for r in revisiones if str(r["transplante_id"]) in trans_ids]
        f_lm = [m for m in lotes_madre if str(m["lote_id"]) in lote_ids]
        lm_ids = {str(m["id"]) for m in f_lm}
        f_um = [u for u in unidades_madre if str(u["lote_madre_id"]) in lm_ids]
        f_ext = [e for e in extracciones if str(e["lote_madre_id"]) in lm_ids]

        return self._compose_dashboard_metrics(
            filtered_props, f_trans, f_revs, f_lm, f_um, f_ext, var_map
        )

    def _filter_propagaciones(
        self,
        items: list[dict[str, Any]],
        fecha_inicio: date | None,
        fecha_fin: date | None,
        variedad_id: str | None,
        tipo_propagacion: str | None,
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for item in items:
            f_siembra = _to_date(item["fecha_siembra"])
            if fecha_inicio and f_siembra < fecha_inicio:
                continue
            if fecha_fin and f_siembra > fecha_fin:
                continue
            if variedad_id and str(item["variedad_id"]) != variedad_id:
                continue
            if tipo_propagacion and str(item["tipo_propagacion"]) != tipo_propagacion:
                continue
            result.append(item)
        return result

    def _compose_dashboard_metrics(
        self,
        props: list[dict[str, Any]],
        trans: list[dict[str, Any]],
        revs: list[dict[str, Any]],
        lotes_madre: list[dict[str, Any]],
        unidades_madre: list[dict[str, Any]],
        extracciones: list[dict[str, Any]],
        var_map: dict[str, str],
    ) -> dict[str, Any]:
        total_sembrado = sum(int(p["cantidad_material"]) for p in props)
        bajas_prop = sum(int(p.get("bajas_propagacion", 0)) for p in props)
        total_procesado = sum(int(t["cantidad_procesada"]) for t in trans)
        saldo_por_trasplantar = max(0, total_sembrado - bajas_prop - total_procesado)

        buenas_bolsa = sum(int(t["cantidad_buenas"]) for t in trans)
        malas_bolsa = sum(int(t["cantidad_malas"]) for t in trans)
        bajas_revision = sum(int(r["contador_malos"]) for r in revs)
        vivas_actual_bolsa = max(0, buenas_bolsa - bajas_revision)
        supervivencia_global = (
            round((buenas_bolsa / total_procesado) * 100, 2) if total_procesado > 0 else 0.0
        )
        alertas_merma = [
            {
                "id": str(t["id"]),
                "codigo_transplante": t["codigo_transplante"],
                "lote_id": str(t["lote_id"]),
                "porcentaje_malas": float(t["porcentaje_malas"]),
                "cantidad_malas": int(t["cantidad_malas"]),
            }
            for t in trans
            if bool(t.get("alerta_merma"))
        ]

        madres_activas = sum(1 for u in unidades_madre if u["estado_planta"] == "ACTIVA")
        total_esquejes = sum(int(e["total_esquejes"]) for e in extracciones)
        total_semillas = sum(int(e["total_semillas"]) for e in extracciones)
        lotes_hijos = sum(1 for p in props if p.get("origen_extraccion_id"))

        supervivencia_lotes = [
            {
                "codigo": t["codigo_transplante"] or str(t["id"])[:8],
                "tipo_lote": t["tipo_lote"],
                "buenas_pct": float(t["porcentaje_buenas"]),
                "malas_pct": float(t["porcentaje_malas"]),
                "alerta_merma": bool(t["alerta_merma"]),
            }
            for t in trans[:12]
        ]

        por_variedad: dict[str, dict[str, Any]] = {}
        for p in props:
            vname = var_map.get(str(p["variedad_id"]), "Sin variedad")
            bucket = por_variedad.setdefault(
                vname, {"variedad": vname, "lotes": 0, "sembrado": 0, "buenas_bolsa": 0}
            )
            bucket["lotes"] += 1
            bucket["sembrado"] += int(p["cantidad_material"])
            for t in trans:
                if str(t["lote_id"]) == str(p["id"]):
                    bucket["buenas_bolsa"] += int(t["cantidad_buenas"])

        return {
            "kpi_propagacion": {
                "total_lotes": len(props),
                "lotes_activos": sum(1 for p in props if p["estado_lote"] != "FINALIZADO"),
                "lotes_finalizados": sum(1 for p in props if p["estado_lote"] == "FINALIZADO"),
                "total_sembrado": total_sembrado,
                "bajas_propagacion": bajas_prop,
                "saldo_disponible": saldo_por_trasplantar,
            },
            "kpi_transplante_bolsa": {
                "total_transplantes": len(trans),
                "total_procesado": total_procesado,
                "buenas_iniciales": buenas_bolsa,
                "malas_transplante": malas_bolsa,
                "revisiones_realizadas": len(revs),
                "bajas_en_revision": bajas_revision,
                "vivas_en_bolsa": vivas_actual_bolsa,
                "supervivencia_pct": supervivencia_global,
                "lotes_en_alerta_merma": len(alertas_merma),
            },
            "kpi_planta_madre": {
                "total_lotes_madre": len(lotes_madre),
                "total_unidades_madre": len(unidades_madre),
                "madres_activas": madres_activas,
                "total_extracciones": len(extracciones),
                "total_esquejes": total_esquejes,
                "total_semillas": total_semillas,
                "lotes_hijos_derivados": lotes_hijos,
            },
            "alertas_merma": alertas_merma,
            "supervivencia_por_transplante": supervivencia_lotes,
            "distribucion_por_variedad": list(por_variedad.values()),
        }

    async def _apply_business_rules(
        self, entity_type: str, data: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        if entity_type == "propagacion":
            return await self._rules_propagacion(data), {}
        if entity_type == "transplante_bolsa":
            return await self._rules_transplante_bolsa(data)
        if entity_type == "revisiones_bolsa":
            await self._rules_revision_bolsa(data)
            return data, {}
        if entity_type == "lotes_planta_madre":
            return await self._rules_lote_madre(data), {}
        if entity_type == "unidades_planta_madre":
            await self._rules_unidad_madre(data)
            return data, {}
        if entity_type == "extracciones_madre":
            return await self._rules_extraccion_madre(data)
        return data, {}

    async def _rules_propagacion(self, data: dict[str, Any]) -> dict[str, Any]:
        trans = await self._repo.list_entities(
            "transplante_bolsa", filters={"lote_id": str(data["id"])}
        )
        procesado = sum(int(t["cantidad_procesada"]) for t in trans)
        estado = validar_propagacion(
            int(data["cantidad_material"]),
            int(data.get("cantidad_plantas_madre", 0)),
            int(data.get("bajas_propagacion", 0)),
            TipoIncorporacion(data["tipo_incorporacion"]),
            str(data.get("proveedor", "")),
            procesado_en_bolsa=procesado,
        )
        data["estado_lote"] = estado.value
        return data

    async def _rules_transplante_bolsa(
        self, data: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        lote = await self._repo.get_entity("propagacion", str(data["lote_id"]))
        if lote is None:
            raise BusinessRuleViolationError("El lote de propagación seleccionado no existe.")
        trans = await self._repo.list_entities(
            "transplante_bolsa", filters={"lote_id": str(data["lote_id"])}
        )
        procesado_otros = sum(
            int(t["cantidad_procesada"]) for t in trans if str(t["id"]) != str(data["id"])
        )
        saldo_disponible = calcular_saldo_propagacion(
            int(lote["cantidad_material"]),
            int(lote.get("bajas_propagacion", 0)),
            procesado_otros,
        )
        res = calcular_transplante_bolsa(
            saldo_disponible=saldo_disponible,
            cantidad_procesada=int(data["cantidad_procesada"]),
            cantidad_buenas=int(data["cantidad_buenas"]),
            fecha_siembra=_to_date(lote["fecha_siembra"]),
            fecha_transplante=_to_date(data["fecha_transplante"]),
        )
        promover = bool(data.pop("promover_planta_madre", False))
        data["cantidad_malas"] = res.cantidad_malas
        data["porcentaje_buenas"] = res.porcentaje_buenas
        data["porcentaje_malas"] = res.porcentaje_malas
        data["alerta_merma"] = res.alerta_merma
        if not data.get("codigo_transplante"):
            data["codigo_transplante"] = f"TP-{str(lote['codigo_lote'])}-{len(trans) + 1:02d}"
        side = {
            "lote": lote,
            "nuevo_estado_lote": res.nuevo_estado_lote.value,
            "promover_planta_madre": promover,
        }
        return data, side

    async def _rules_revision_bolsa(self, data: dict[str, Any]) -> None:
        tp = await self._repo.get_entity("transplante_bolsa", str(data["transplante_id"]))
        if tp is None:
            raise BusinessRuleViolationError("El trasplante a bolsa indicado no existe.")
        revs = await self._repo.list_entities(
            "revisiones_bolsa", filters={"transplante_id": str(data["transplante_id"])}
        )
        malos_previos = sum(
            int(r["contador_malos"]) for r in revs if str(r["id"]) != str(data["id"])
        )
        validar_revision_bolsa(
            fecha_transplante=_to_date(tp["fecha_transplante"]),
            fecha_revision=_to_date(data["fecha_revision"]),
            unidades_revisadas=int(data["unidades_revisadas"]),
            contador_buenos=int(data["contador_buenos"]),
            contador_malos=int(data["contador_malos"]),
            buenas_totales_transplante=int(tp["cantidad_buenas"]),
            malos_acumulados_previos=malos_previos,
        )

    async def _rules_lote_madre(self, data: dict[str, Any]) -> dict[str, Any]:
        lote = await self._repo.get_entity("propagacion", str(data["lote_id"]))
        if lote is None:
            raise BusinessRuleViolationError("El lote origen para Planta Madre no existe.")
        if data.get("cantidad_madres_activas") is None:
            data["cantidad_madres_activas"] = int(data["cantidad_madres_inicial"])
        return data

    async def _rules_unidad_madre(self, data: dict[str, Any]) -> None:
        lote_madre = await self._repo.get_entity("lotes_planta_madre", str(data["lote_madre_id"]))
        if lote_madre is None:
            raise BusinessRuleViolationError("El lote de plantas madre no existe.")
        if not data.get("codigo_planta"):
            data["codigo_planta"] = f"PM-{int(data['numero_planta']):03d}"

    async def _rules_extraccion_madre(
        self, data: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        lm = await self._repo.get_entity("lotes_planta_madre", str(data["lote_madre_id"]))
        if lm is None:
            raise BusinessRuleViolationError("El lote de planta madre no existe.")
        unidades = await self._repo.list_entities(
            "unidades_planta_madre", filters={"lote_madre_id": str(lm["id"])}
        )
        by_num = {int(u["numero_planta"]): u for u in unidades}
        for row in data["detalle_plantas"]:
            num = int(row["numero_planta"])
            unidad = by_num.get(num)
            if unidad and unidad["estado_planta"] == EstadoPlantaMadre.DESCARTADA.value:
                raise BusinessRuleViolationError(
                    f"La planta madre #{num} está DESCARTADA y no admite extracciones."
                )

        totales = validar_extraccion_madre(
            fecha_transplante_ref=_to_date(data["fecha_transplante_ref"]),
            fecha_extraccion=_to_date(data["fecha_extraccion"]),
            detalle_plantas=data["detalle_plantas"],
        )
        data["total_esquejes"] = totales.total_esquejes
        data["total_semillas"] = totales.total_semillas
        return data, {"lote_madre": lm, "unidades_by_num": by_num}

    async def _execute_side_effects(
        self,
        entity_type: str,
        saved: dict[str, Any],
        side: dict[str, Any],
        actor: Usuario,
        correlation_id: str,
        source: SyncSource,
    ) -> None:
        if entity_type == "transplante_bolsa" and side:
            await self._sync_propagacion_after_transplante(saved, side)
            if (
                source == SyncSource.ONLINE
                and side.get("promover_planta_madre")
                and saved["tipo_lote"] == TipoLoteTransplante.PLANTA_MADRE.value
                and int(saved["cantidad_buenas"]) > 0
            ):
                await self._promote_transplante_to_mothers(saved, side["lote"])
        elif entity_type == "unidades_planta_madre" and source == SyncSource.ONLINE:
            await self._refresh_lote_madre_active_count(str(saved["lote_madre_id"]))
        elif entity_type == "extracciones_madre" and side and source == SyncSource.ONLINE:
            await self._update_unidades_after_extraccion(saved, side["unidades_by_num"])
            await self._derive_child_lot_if_needed(saved, side["lote_madre"], actor, correlation_id)

    async def _sync_propagacion_after_transplante(
        self, tp: dict[str, Any], side: dict[str, Any]
    ) -> None:
        lote = dict(side["lote"])
        nuevo_estado = side["nuevo_estado_lote"]
        if lote["estado_lote"] != nuevo_estado:
            lote["estado_lote"] = nuevo_estado
            lote["version"] = int(lote["version"]) + 1
            await self._repo.upsert_entity("propagacion", lote)

    async def _promote_transplante_to_mothers(
        self, tp: dict[str, Any], lote: dict[str, Any]
    ) -> None:
        existing = await self._repo.list_entities(
            "lotes_planta_madre", filters={"lote_id": str(tp["lote_id"])}
        )
        already = [m for m in existing if m.get("transplante_bolsa_id") == tp["id"]]
        if already:
            return
        lm_id = str(uuid4())
        count = int(tp["cantidad_buenas"])
        lm_record = await self._repo.upsert_entity(
            "lotes_planta_madre",
            {
                "id": lm_id,
                "lote_id": str(tp["lote_id"]),
                "transplante_bolsa_id": str(tp["id"]),
                "fecha_establecimiento": tp["fecha_transplante"],
                "ubicacion_id": str(tp["ubicacion_id"]),
                "cantidad_madres_inicial": count,
                "cantidad_madres_activas": count,
                "observaciones": f"Promovido automáticamente desde {tp['codigo_transplante']}",
                "version": 1,
            },
        )
        # Crea hasta 20 unidades individuales numeradas por defecto para gestión directa CV-09
        unidades_crear = min(count, 20)
        for idx in range(1, unidades_crear + 1):
            await self._repo.upsert_entity(
                "unidades_planta_madre",
                {
                    "id": str(uuid4()),
                    "lote_madre_id": str(lm_record["id"]),
                    "numero_planta": idx,
                    "codigo_planta": f"PM-{lote['codigo_lote']}-{idx:03d}",
                    "estado_planta": EstadoPlantaMadre.ACTIVA.value,
                    "total_esquejes": 0,
                    "total_semillas": 0,
                    "observaciones": "Alta inicial desde transplante a bolsa",
                    "version": 1,
                },
            )

    async def _refresh_lote_madre_active_count(self, lote_madre_id: str) -> None:
        lm = await self._repo.get_entity("lotes_planta_madre", lote_madre_id)
        if not lm:
            return
        unidades = await self._repo.list_entities(
            "unidades_planta_madre", filters={"lote_madre_id": lote_madre_id}
        )
        if not unidades:
            return
        activas = sum(
            1 for u in unidades if u["estado_planta"] != EstadoPlantaMadre.DESCARTADA.value
        )
        lm["cantidad_madres_activas"] = activas
        lm["version"] = int(lm["version"]) + 1
        await self._repo.upsert_entity("lotes_planta_madre", lm)

    async def _update_unidades_after_extraccion(
        self, ext: dict[str, Any], units_by_num: dict[int, dict[str, Any]]
    ) -> None:
        all_ext = await self._repo.list_entities(
            "extracciones_madre", filters={"lote_madre_id": str(ext["lote_madre_id"])}
        )
        esq_sum: dict[int, int] = {}
        sem_sum: dict[int, int] = {}
        last_dt: dict[int, str] = {}
        for item in all_ext:
            dt_str = str(item["fecha_extraccion"])
            for row in item.get("detalle_plantas", []):
                num = int(row["numero_planta"])
                esq_sum[num] = esq_sum.get(num, 0) + int(row.get("esquejes", 0))
                sem_sum[num] = sem_sum.get(num, 0) + int(row.get("semillas", 0))
                if num not in last_dt or dt_str > last_dt[num]:
                    last_dt[num] = dt_str

        for num, u in units_by_num.items():
            updated_u = dict(u)
            updated_u["total_esquejes"] = esq_sum.get(num, 0)
            updated_u["total_semillas"] = sem_sum.get(num, 0)
            updated_u["ultima_extraccion"] = (
                date.fromisoformat(last_dt[num][:10]) if num in last_dt else None
            )
            updated_u["version"] = int(updated_u["version"]) + 1
            await self._repo.upsert_entity("unidades_planta_madre", updated_u)

    async def _derive_child_lot_if_needed(
        self,
        ext: dict[str, Any],
        lote_madre: dict[str, Any],
        actor: Usuario,
        correlation_id: str,
    ) -> None:
        codigo_hijo = str(ext.get("lote_hijo_codigo") or "").strip()
        if not codigo_hijo:
            return
        props = await self._repo.list_entities("propagacion")
        if any(p["codigo_lote"] == codigo_hijo for p in props):
            return
        lote_padre = await self._repo.get_entity("propagacion", str(lote_madre["lote_id"]))
        if not lote_padre:
            return
        total_esq = int(ext["total_esquejes"])
        total_sem = int(ext["total_semillas"])
        tipo_prop = (
            TipoPropagacion.ESQUEJE if total_esq >= total_sem else TipoPropagacion.SEMILLA
        )
        await self.create_or_update(
            actor,
            "propagacion",
            {
                "id": str(uuid4()),
                "codigo_lote": codigo_hijo,
                "fecha_siembra": str(ext["fecha_extraccion"]),
                "variedad_id": str(lote_padre["variedad_id"]),
                "ubicacion_id": lote_madre.get("ubicacion_id") or lote_padre.get("ubicacion_id"),
                "responsable_id": ext.get("responsable_id") or actor.funcionario_id,
                "tipo_propagacion": tipo_prop.value,
                "tipo_incorporacion": TipoIncorporacion.PROPIA.value,
                "origen_extraccion_id": str(ext["id"]),
                "proveedor": "",
                "cantidad_material": total_esq + total_sem,
                "cantidad_plantas_madre": 0,
                "bajas_propagacion": 0,
                "estado_lote": EstadoLote.SIEMBRA.value,
                "observaciones": f"Lote hijo derivado de extracción en {lote_padre['codigo_lote']}",
            },
            correlation_id=correlation_id,
            source=SyncSource.ONLINE,
        )

    async def _recalculate_after_delete(
        self, entity_type: str, deleted_before: dict[str, Any]
    ) -> None:
        if entity_type != "transplante_bolsa":
            return
        lote = await self._repo.get_entity("propagacion", str(deleted_before["lote_id"]))
        if lote is None:
            return
        await self._rules_propagacion(dict(lote))
        lote_upd = dict(lote)
        lote_upd["estado_lote"] = validar_propagacion(
            int(lote["cantidad_material"]),
            int(lote.get("cantidad_plantas_madre", 0)),
            int(lote.get("bajas_propagacion", 0)),
            TipoIncorporacion(lote["tipo_incorporacion"]),
            str(lote.get("proveedor", "")),
            procesado_en_bolsa=sum(
                int(t["cantidad_procesada"])
                for t in await self._repo.list_entities(
                    "transplante_bolsa", filters={"lote_id": str(lote["id"])}
                )
            ),
        ).value
        lote_upd["version"] = int(lote_upd["version"]) + 1
        await self._repo.upsert_entity("propagacion", lote_upd)
