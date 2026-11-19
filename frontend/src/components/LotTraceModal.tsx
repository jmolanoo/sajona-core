import React from "react";
import { GitBranch, Layers, Package, Sprout } from "lucide-react";
import { calcularSaldoPropagacion } from "../domain/calculations";
import type {
  ExtraccionMadre,
  LotePlantaMadre,
  Propagacion,
  RevisionBolsa,
  TransplanteBolsa,
  UnidadPlantaMadre,
  Variedad,
} from "../domain/types";
import { Modal } from "./UiPrimitives";

export const LotTraceModal: React.FC<{
  lote: Propagacion | null;
  variedades: Variedad[];
  propagaciones: Propagacion[];
  transplantes: TransplanteBolsa[];
  revisiones: RevisionBolsa[];
  lotesMadre: LotePlantaMadre[];
  unidadesMadre: UnidadPlantaMadre[];
  extracciones: ExtraccionMadre[];
  onClose: () => void;
}> = ({
  lote,
  variedades,
  propagaciones,
  transplantes,
  revisiones,
  lotesMadre,
  unidadesMadre,
  extracciones,
  onClose,
}) => {
  if (!lote) return null;

  const varName = variedades.find((v) => v.id === lote.variedad_id)?.nombre || "N/A";
  const loteTrans = transplantes.filter((t) => t.lote_id === lote.id);
  const tpIds = new Set(loteTrans.map((t) => t.id));
  const loteRevs = revisiones.filter((r) => tpIds.has(r.transplante_id));
  const loteMadres = lotesMadre.filter((m) => m.lote_id === lote.id);
  const lmIds = new Set(loteMadres.map((m) => m.id));
  const loteUnits = unidadesMadre.filter((u) => lmIds.has(u.lote_madre_id));
  const loteExts = extracciones.filter((e) => lmIds.has(e.lote_madre_id));
  const extIds = new Set(loteExts.map((e) => e.id));
  const hijos = propagaciones.filter(
    (p) => p.origen_extraccion_id && extIds.has(p.origen_extraccion_id)
  );
  const saldoDisp = calcularSaldoPropagacion(lote, transplantes);
  const totalBuenasBolsa = loteTrans.reduce((s, t) => s + Number(t.cantidad_buenas || 0), 0);
  const totalBajasRev = loteRevs.reduce((s, r) => s + Number(r.contador_malos || 0), 0);

  return (
    <Modal
      open={Boolean(lote)}
      onClose={onClose}
      title={`Trazabilidad Integral 360° — ${lote.codigo_lote}`}
      subtitle={`${varName} • ${lote.tipo_propagacion} (${lote.tipo_incorporacion}) • Funciona online y offline`}
      wide
    >
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
        <div className="rounded-lg border border-slate-200 p-2.5 bg-slate-50">
          <span className="text-slate-500">Sembrado / Saldo Prop.</span>
          <div className="font-bold text-sm text-slate-900 mt-0.5">
            {lote.cantidad_material} / {saldoDisp} disp.
          </div>
        </div>
        <div className="rounded-lg border border-slate-200 p-2.5 bg-slate-50">
          <span className="text-slate-500">Vivas en Bolsa (neto)</span>
          <div className="font-bold text-sm text-emerald-700 mt-0.5">
            {Math.max(0, totalBuenasBolsa - totalBajasRev)} uds
          </div>
        </div>
        <div className="rounded-lg border border-slate-200 p-2.5 bg-slate-50">
          <span className="text-slate-500">Plantas Madre Reg.</span>
          <div className="font-bold text-sm text-slate-900 mt-0.5">{loteUnits.length} uds</div>
        </div>
        <div className="rounded-lg border border-slate-200 p-2.5 bg-slate-50">
          <span className="text-slate-500">Clones / Hijos Derivados</span>
          <div className="font-bold text-sm text-slate-900 mt-0.5">{hijos.length} lotes</div>
        </div>
      </div>

      <div className="space-y-3 text-xs">
        <div className="rounded-xl border border-slate-200 p-3 space-y-1">
          <div className="font-bold text-slate-800 flex items-center gap-1.5">
            <Sprout className="w-4 h-4 text-emerald-700" /> Módulo 1: Propagación ({lote.estado_lote})
          </div>
          <p className="text-slate-600">
            Siembra: <strong>{lote.fecha_siembra}</strong> • Bajas en cámara:{" "}
            <strong>{lote.bajas_propagacion}</strong>{" "}
            {lote.origen_extraccion_id ? "• Lote hijo derivado de extracción madre." : ""}
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 p-3 space-y-2">
          <div className="font-bold text-slate-800 flex items-center gap-1.5">
            <Package className="w-4 h-4 text-blue-700" /> Módulo 3: Transplantes a Bolsa (
            {loteTrans.length}) y Revisiones Periódicas ({loteRevs.length})
          </div>
          {loteTrans.length === 0 ? (
            <p className="text-slate-500">Sin trasplantes a bolsa registrados.</p>
          ) : (
            loteTrans.map((t) => (
              <div key={t.id} className="rounded-lg bg-slate-50 p-2 border border-slate-200">
                <div className="flex flex-wrap justify-between gap-2 font-semibold">
                  <span>
                    {t.codigo_transplante} ({t.fecha_transplante}) • {t.tipo_lote}
                  </span>
                  <span className={t.alerta_merma ? "text-red-700" : "text-emerald-700"}>
                    Buenas: {t.cantidad_buenas}/{t.cantidad_procesada} ({t.porcentaje_buenas}% | Merma{" "}
                    {t.porcentaje_malas}%)
                  </span>
                </div>
              </div>
            ))
          )}
          {loteRevs.length > 0 && (
            <div className="text-slate-600 pt-1">
              Revisiones periódicas: {loteRevs.length} registradas ({totalBajasRev} bajas detectadas).
            </div>
          )}
        </div>

        <div className="rounded-xl border border-slate-200 p-3 space-y-2">
          <div className="font-bold text-slate-800 flex items-center gap-1.5">
            <Layers className="w-4 h-4 text-red-700" /> Módulo 2: Plantas Madre y Extracciones (
            {loteExts.length})
          </div>
          {loteExts.length === 0 ? (
            <p className="text-slate-500">Sin extracciones registradas en este lote.</p>
          ) : (
            loteExts.map((e) => (
              <div key={e.id} className="rounded-lg bg-slate-50 p-2 border border-slate-200">
                Fecha {e.fecha_extraccion}: <strong>{e.total_esquejes} esquejes</strong> y{" "}
                <strong>{e.total_semillas} semillas</strong>{" "}
                {e.lote_hijo_codigo ? `-> Derivó lote ${e.lote_hijo_codigo}` : ""}
              </div>
            ))
          )}
        </div>

        {hijos.length > 0 && (
          <div className="rounded-xl border border-emerald-200 bg-emerald-50/40 p-3 space-y-1">
            <div className="font-bold text-emerald-900 flex items-center gap-1.5">
              <GitBranch className="w-4 h-4" /> Descendencia Genética Directa
            </div>
            {hijos.map((h) => (
              <div key={h.id} className="text-emerald-800">
                • <strong>{h.codigo_lote}</strong> ({h.fecha_siembra}) — {h.cantidad_material}{" "}
                unidades ({h.tipo_propagacion})
              </div>
            ))}
          </div>
        )}
      </div>
    </Modal>
  );
};
