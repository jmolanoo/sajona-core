import type {
  DashboardSummary,
  ExtraccionMadre,
  LotePlantaMadre,
  Propagacion,
  RevisionBolsa,
  TransplanteBolsa,
  UnidadPlantaMadre,
  Variedad,
} from "./types";

export interface DashboardFilter {
  fechaInicio?: string;
  fechaFin?: string;
  variedadId?: string;
  tipoPropagacion?: string;
}

export function computeLocalDashboardSummary(
  data: {
    propagaciones: Propagacion[];
    transplantes: TransplanteBolsa[];
    revisiones: RevisionBolsa[];
    lotesMadre: LotePlantaMadre[];
    unidadesMadre: UnidadPlantaMadre[];
    extracciones: ExtraccionMadre[];
    variedades: Variedad[];
  },
  filter: DashboardFilter = {}
): DashboardSummary {
  const varMap = new Map(data.variedades.map((v) => [v.id, v.nombre]));
  const props = data.propagaciones.filter((p) => {
    if (p.deleted_at) return false;
    if (filter.fechaInicio && p.fecha_siembra < filter.fechaInicio) return false;
    if (filter.fechaFin && p.fecha_siembra > filter.fechaFin) return false;
    if (filter.variedadId && p.variedad_id !== filter.variedadId) return false;
    if (filter.tipoPropagacion && p.tipo_propagacion !== filter.tipoPropagacion) return false;
    return true;
  });

  const propIds = new Set(props.map((p) => p.id));
  const trans = data.transplantes.filter((t) => !t.deleted_at && propIds.has(t.lote_id));
  const transIds = new Set(trans.map((t) => t.id));
  const revs = data.revisiones.filter((r) => !r.deleted_at && transIds.has(r.transplante_id));
  const lotesMadre = data.lotesMadre.filter((m) => !m.deleted_at && propIds.has(m.lote_id));
  const lmIds = new Set(lotesMadre.map((m) => m.id));
  const unidades = data.unidadesMadre.filter((u) => !u.deleted_at && lmIds.has(u.lote_madre_id));
  const exts = data.extracciones.filter((e) => !e.deleted_at && lmIds.has(e.lote_madre_id));

  const totalSembrado = props.reduce((s, p) => s + Number(p.cantidad_material || 0), 0);
  const bajasProp = props.reduce((s, p) => s + Number(p.bajas_propagacion || 0), 0);
  const totalProcesado = trans.reduce((s, t) => s + Number(t.cantidad_procesada || 0), 0);
  const buenasBolsa = trans.reduce((s, t) => s + Number(t.cantidad_buenas || 0), 0);
  const malasBolsa = trans.reduce((s, t) => s + Number(t.cantidad_malas || 0), 0);
  const bajasRev = revs.reduce((s, r) => s + Number(r.contador_malos || 0), 0);

  const alertas = trans
    .filter((t) => t.alerta_merma)
    .map((t) => ({
      id: t.id,
      codigo_transplante: t.codigo_transplante,
      lote_id: t.lote_id,
      porcentaje_malas: Number(t.porcentaje_malas),
      cantidad_malas: Number(t.cantidad_malas),
    }));

  const byVar = new Map<string, { variedad: string; lotes: number; sembrado: number; buenas_bolsa: number }>();
  for (const p of props) {
    const vName = varMap.get(p.variedad_id) || "Sin variedad";
    const row = byVar.get(vName) || { variedad: vName, lotes: 0, sembrado: 0, buenas_bolsa: 0 };
    row.lotes += 1;
    row.sembrado += Number(p.cantidad_material || 0);
    row.buenas_bolsa += trans
      .filter((t) => t.lote_id === p.id)
      .reduce((acc, t) => acc + Number(t.cantidad_buenas || 0), 0);
    byVar.set(vName, row);
  }

  return {
    kpi_propagacion: {
      total_lotes: props.length,
      lotes_activos: props.filter((p) => p.estado_lote !== "FINALIZADO").length,
      lotes_finalizados: props.filter((p) => p.estado_lote === "FINALIZADO").length,
      total_sembrado: totalSembrado,
      bajas_propagacion: bajasProp,
      saldo_disponible: Math.max(0, totalSembrado - bajasProp - totalProcesado),
    },
    kpi_transplante_bolsa: {
      total_transplantes: trans.length,
      total_procesado: totalProcesado,
      buenas_iniciales: buenasBolsa,
      malas_transplante: malasBolsa,
      revisiones_realizadas: revs.length,
      bajas_en_revision: bajasRev,
      vivas_en_bolsa: Math.max(0, buenasBolsa - bajasRev),
      supervivencia_pct: totalProcesado > 0 ? Math.round((buenasBolsa / totalProcesado) * 10000) / 100 : 0,
      lotes_en_alerta_merma: alertas.length,
    },
    kpi_planta_madre: {
      total_lotes_madre: lotesMadre.length,
      total_unidades_madre: unidades.length,
      madres_activas: unidades.filter((u) => u.estado_planta === "ACTIVA").length,
      total_extracciones: exts.length,
      total_esquejes: exts.reduce((s, e) => s + Number(e.total_esquejes || 0), 0),
      total_semillas: exts.reduce((s, e) => s + Number(e.total_semillas || 0), 0),
      lotes_hijos_derivados: props.filter((p) => Boolean(p.origen_extraccion_id)).length,
    },
    alertas_merma: alertas,
    supervivencia_por_transplante: trans.slice(0, 12).map((t) => ({
      codigo: t.codigo_transplante || t.id.slice(0, 8),
      tipo_lote: t.tipo_lote,
      buenas_pct: Number(t.porcentaje_buenas),
      malas_pct: Number(t.porcentaje_malas),
      alerta_merma: Boolean(t.alerta_merma),
    })),
    distribucion_por_variedad: Array.from(byVar.values()),
  };
}
