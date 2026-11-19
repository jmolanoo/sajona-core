import React, { useMemo, useState } from "react";
import { AlertTriangle, ArrowRight, Eye, Package, Sprout, Trees } from "lucide-react";
import type { CoreRouteId } from "../components/AppShell";
import { ExportToolbar } from "../components/UiPrimitives";
import { useEntityRecords, useOnlineStatus } from "../db/useLocalData";
import { calcularSaldoPropagacion } from "../domain/calculations";
import { computeLocalDashboardSummary } from "../domain/dashboardStats";
import type {
  ExtraccionMadre,
  LotePlantaMadre,
  Propagacion,
  RevisionBolsa,
  TransplanteBolsa,
  UnidadPlantaMadre,
  Variedad,
} from "../domain/types";

export const DashboardPage: React.FC<{
  onNavigate: (r: CoreRouteId) => void;
  onInspectLot: (lote: Propagacion) => void;
}> = ({ onNavigate, onInspectLot }) => {
  const online = useOnlineStatus();
  const { rows: propagaciones } = useEntityRecords<Propagacion>("propagacion");
  const { rows: transplantes } = useEntityRecords<TransplanteBolsa>("transplante_bolsa");
  const { rows: revisiones } = useEntityRecords<RevisionBolsa>("revisiones_bolsa");
  const { rows: lotesMadre } = useEntityRecords<LotePlantaMadre>("lotes_planta_madre");
  const { rows: unidadesMadre } = useEntityRecords<UnidadPlantaMadre>("unidades_planta_madre");
  const { rows: extracciones } = useEntityRecords<ExtraccionMadre>("extracciones_madre");
  const { rows: variedades } = useEntityRecords<Variedad>("variedades");

  const [fechaInicio, setFechaInicio] = useState("");
  const [fechaFin, setFechaFin] = useState("");
  const [variedadId, setVariedadId] = useState("");
  const [tipoProp, setTipoProp] = useState("");

  const summary = useMemo(
    () =>
      computeLocalDashboardSummary(
        {
          propagaciones,
          transplantes,
          revisiones,
          lotesMadre,
          unidadesMadre,
          extracciones,
          variedades,
        },
        {
          fechaInicio: fechaInicio || undefined,
          fechaFin: fechaFin || undefined,
          variedadId: variedadId || undefined,
          tipoPropagacion: tipoProp || undefined,
        }
      ),
    [
      propagaciones,
      transplantes,
      revisiones,
      lotesMadre,
      unidadesMadre,
      extracciones,
      variedades,
      fechaInicio,
      fechaFin,
      variedadId,
      tipoProp,
    ]
  );

  const varMap = useMemo(() => new Map(variedades.map((v) => [v.id, v.nombre])), [variedades]);

  const funnelStages = [
    { label: "Sembrado (Prop.)", value: summary.kpi_propagacion.total_sembrado, color: "#15803d" },
    {
      label: "Procesado a Bolsa",
      value: summary.kpi_transplante_bolsa.total_procesado,
      color: "#1d4ed8",
    },
    {
      label: "Vivas en Bolsa",
      value: summary.kpi_transplante_bolsa.vivas_en_bolsa,
      color: "#0f766e",
    },
    {
      label: "Madres Activas",
      value: summary.kpi_planta_madre.madres_activas,
      color: "#8B1D1D",
    },
    {
      label: "Material Clonado",
      value: summary.kpi_planta_madre.total_esquejes + summary.kpi_planta_madre.total_semillas,
      color: "#7c3aed",
    },
  ];
  const maxFunnel = Math.max(1, ...funnelStages.map((s) => s.value));

  const exportRows = propagaciones.map((p) => {
    const tLote = transplantes.filter((t) => t.lote_id === p.id);
    const proc = tLote.reduce((a, t) => a + t.cantidad_procesada, 0);
    const buenas = tLote.reduce((a, t) => a + t.cantidad_buenas, 0);
    const malas = tLote.reduce((a, t) => a + t.cantidad_malas, 0);
    const saldo = calcularSaldoPropagacion(p, transplantes);
    return [
      p.codigo_lote,
      p.fecha_siembra,
      varMap.get(p.variedad_id) || "N/A",
      p.tipo_propagacion,
      p.cantidad_material,
      saldo,
      proc,
      buenas,
      malas,
      p.estado_lote,
    ];
  });

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900">
            Dashboard Operativo SAJONA
          </h1>
          <p className="text-xs sm:text-sm text-slate-600">
            Analítica en tiempo real sobre Propagación, Planta Madre y Transplante a Bolsa (
            {online ? "Conectado" : "Cálculo Local Offline"}).
          </p>
        </div>
        <ExportToolbar
          title="Consolidado_Nucleo_SAJONA"
          columns={[
            "Lote",
            "Siembra",
            "Variedad",
            "Tipo Prop.",
            "Sembrado",
            "Saldo Prop.",
            "En Bolsa",
            "Buenas",
            "Malas",
            "Estado",
          ]}
          rows={exportRows}
        />
      </div>

      {/* Filtros analíticos */}
      <div className="bg-white rounded-2xl border border-slate-200 p-3 sm:p-4 shadow-sm grid grid-cols-1 sm:grid-cols-4 gap-3">
        <div>
          <label htmlFor="dash-fi" className="block text-[11px] font-bold text-slate-600 mb-1">Fecha Inicio</label>
          <input
            id="dash-fi"
            type="date"
            value={fechaInicio}
            onChange={(e) => setFechaInicio(e.target.value)}
            className="w-full rounded-xl border border-slate-300 px-3 py-2 text-xs"
          />
        </div>
        <div>
          <label htmlFor="dash-ff" className="block text-[11px] font-bold text-slate-600 mb-1">Fecha Fin</label>
          <input
            id="dash-ff"
            type="date"
            value={fechaFin}
            onChange={(e) => setFechaFin(e.target.value)}
            className="w-full rounded-xl border border-slate-300 px-3 py-2 text-xs"
          />
        </div>
        <div>
          <label htmlFor="dash-var" className="block text-[11px] font-bold text-slate-600 mb-1">Variedad</label>
          <select
            id="dash-var"
            value={variedadId}
            onChange={(e) => setVariedadId(e.target.value)}
            className="w-full rounded-xl border border-slate-300 px-3 py-2 text-xs bg-white"
          >
            <option value="">Todas las variedades</option>
            {variedades.map((v) => (
              <option key={v.id} value={v.id}>
                {v.nombre}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="dash-tipo" className="block text-[11px] font-bold text-slate-600 mb-1">
            Tipo de Propagación
          </label>
          <select
            id="dash-tipo"
            value={tipoProp}
            onChange={(e) => setTipoProp(e.target.value)}
            className="w-full rounded-xl border border-slate-300 px-3 py-2 text-xs bg-white"
          >
            <option value="">Todos</option>
            <option value="ESQUEJE">ESQUEJE</option>
            <option value="SEMILLA">SEMILLA</option>
            <option value="IN_VITRO">IN_VITRO</option>
          </select>
        </div>
      </div>

      {/* Tarjetas KPI de los 3 módulos */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="rounded-2xl bg-emerald-50 border border-emerald-200 p-4">
          <div className="flex items-center justify-between text-xs font-bold text-emerald-800">
            <span>PROPAGACIÓN</span>
            <Sprout className="w-4 h-4" />
          </div>
          <div className="text-2xl font-extrabold text-emerald-950 mt-1">
            {summary.kpi_propagacion.total_lotes} lotes
          </div>
          <div className="text-xs text-emerald-800 mt-0.5">
            Saldo disp.: <strong>{summary.kpi_propagacion.saldo_disponible}</strong> /{" "}
            {summary.kpi_propagacion.total_sembrado} uds
          </div>
        </div>

        <div className="rounded-2xl bg-blue-50 border border-blue-200 p-4">
          <div className="flex items-center justify-between text-xs font-bold text-blue-800">
            <span>TRANSPLANTE BOLSA</span>
            <Package className="w-4 h-4" />
          </div>
          <div className="text-2xl font-extrabold text-blue-950 mt-1">
            {summary.kpi_transplante_bolsa.supervivencia_pct}%
          </div>
          <div className="text-xs text-blue-800 mt-0.5">
            Vivas hoy: <strong>{summary.kpi_transplante_bolsa.vivas_en_bolsa}</strong> (
            {summary.kpi_transplante_bolsa.revisiones_realizadas} rev.)
          </div>
        </div>

        <div className="rounded-2xl bg-purple-50 border border-purple-200 p-4">
          <div className="flex items-center justify-between text-xs font-bold text-purple-800">
            <span>PLANTAS MADRE</span>
            <Trees className="w-4 h-4" />
          </div>
          <div className="text-2xl font-extrabold text-purple-950 mt-1">
            {summary.kpi_planta_madre.total_esquejes + summary.kpi_planta_madre.total_semillas}
          </div>
          <div className="text-xs text-purple-800 mt-0.5">
            {summary.kpi_planta_madre.total_esquejes} esq. / {summary.kpi_planta_madre.total_semillas}{" "}
            sem. • {summary.kpi_planta_madre.lotes_hijos_derivados} hijos
          </div>
        </div>

        <div
          className={`rounded-2xl border p-4 ${
            summary.kpi_transplante_bolsa.lotes_en_alerta_merma > 0
              ? "bg-red-50 border-red-200 text-red-900"
              : "bg-slate-50 border-slate-200 text-slate-900"
          }`}
        >
          <div className="flex items-center justify-between text-xs font-bold">
            <span>ALERTAS MERMA &gt;20%</span>
            <AlertTriangle className="w-4 h-4" />
          </div>
          <div className="text-2xl font-extrabold mt-1">
            {summary.kpi_transplante_bolsa.lotes_en_alerta_merma}
          </div>
          <div className="text-xs mt-0.5">
            Merma total bolsa: {summary.kpi_transplante_bolsa.malas_transplante} uds
          </div>
        </div>
      </div>

      {/* Gráficas SVG reales */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm space-y-3">
          <h2 className="text-sm font-bold text-slate-900">
            Embudo de Conversión Agronómica (Módulos 1–3)
          </h2>
          <svg
            viewBox="0 0 420 185"
            className="w-full h-48"
            role="img"
            aria-label="Embudo cuantitativo de Propagación a Bolsa y Plantas Madre"
          >
            {funnelStages.map((st, idx) => {
              const y = 10 + idx * 34;
              const barW = Math.max(8, Math.round((st.value / maxFunnel) * 210));
              return (
                <g key={st.label}>
                  <text x="4" y={y + 16} fontSize="11" fill="#334155" fontWeight="600">
                    {st.label}
                  </text>
                  <rect x="145" y={y + 2} width="210" height="20" rx="5" fill="#f1f5f9" />
                  <rect x="145" y={y + 2} width={barW} height="20" rx="5" fill={st.color} />
                  <text x="364" y={y + 16} fontSize="11" fill="#0f172a" fontWeight="700">
                    {st.value}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm space-y-3">
          <h2 className="text-sm font-bold text-slate-900">
            Supervivencia vs. Merma (%) por Trasplante a Bolsa
          </h2>
          {summary.supervivencia_por_transplante.length === 0 ? (
            <p className="text-xs text-slate-500 py-8 text-center">
              Sin trasplantes en el rango filtrado.
            </p>
          ) : (
            <div className="space-y-2.5">
              {summary.supervivencia_por_transplante.map((item) => (
                <div key={item.codigo} className="space-y-1 text-xs">
                  <div className="flex justify-between font-semibold">
                    <span>
                      {item.codigo}{" "}
                      <span className="text-slate-500 font-normal">({item.tipo_lote})</span>
                    </span>
                    <span className={item.alerta_merma ? "text-red-700 font-bold" : "text-emerald-700"}>
                      {item.buenas_pct}% buenas • {item.malas_pct}% merma
                    </span>
                  </div>
                  <div className="w-full h-2.5 bg-red-100 rounded-full overflow-hidden flex">
                    <div
                      style={{ width: `${item.buenas_pct}%` }}
                      className={item.alerta_merma ? "bg-amber-600 h-full" : "bg-emerald-600 h-full"}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Accesos rápidos a los 3 módulos */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm space-y-3">
        <h2 className="text-sm font-bold text-slate-900">Accesos Rápidos a Módulos</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <button
            type="button"
            onClick={() => onNavigate("propagacion")}
            className="flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3 text-left hover:bg-slate-50"
          >
            <div>
              <div className="text-sm font-bold text-slate-900">1. Propagación</div>
              <div className="text-xs text-slate-500">Siembra por lote y saldo disponible</div>
            </div>
            <ArrowRight className="w-4 h-4 text-slate-400" />
          </button>
          <button
            type="button"
            onClick={() => onNavigate("planta_madre")}
            className="flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3 text-left hover:bg-slate-50"
          >
            <div>
              <div className="text-sm font-bold text-slate-900">2. Planta Madre</div>
              <div className="text-xs text-slate-500">Extracciones CV-09 e hijos genéticos</div>
            </div>
            <ArrowRight className="w-4 h-4 text-slate-400" />
          </button>
          <button
            type="button"
            onClick={() => onNavigate("transplante_bolsa")}
            className="flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3 text-left hover:bg-slate-50"
          >
            <div>
              <div className="text-sm font-bold text-slate-900">3. Transplante a Bolsa</div>
              <div className="text-xs text-slate-500">Supervivencia, alertas y revisión CV-05</div>
            </div>
            <ArrowRight className="w-4 h-4 text-slate-400" />
          </button>
        </div>
      </div>

      {/* Listado de trazabilidad directa */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm space-y-3">
        <h2 className="text-sm font-bold text-slate-900">
          Trazabilidad Rápida por Lote ({propagaciones.length})
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {propagaciones.map((lote) => {
            const saldo = calcularSaldoPropagacion(lote, transplantes);
            return (
              <div
                key={lote.id}
                className="rounded-xl border border-slate-200 p-3 flex items-center justify-between gap-2 bg-slate-50/50"
              >
                <div className="min-w-0">
                  <div className="font-bold text-sm text-slate-900 truncate">{lote.codigo_lote}</div>
                  <div className="text-xs text-slate-600 truncate">
                    {varMap.get(lote.variedad_id) || "N/A"} • Saldo: <strong>{saldo}</strong>/
                    {lote.cantidad_material}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => onInspectLot(lote)}
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-900 text-white text-xs font-semibold shrink-0"
                >
                  <Eye className="w-3.5 h-3.5" /> Ver Traza
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
