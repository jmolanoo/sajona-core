import React, { useEffect, useMemo, useState } from "react";
import { AlertTriangle, ClipboardCheck, Plus, Trash2 } from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { EmptyState, ExportToolbar, Modal, SyncStatusBadge } from "../components/UiPrimitives";
import { db } from "../db/schema";
import { queueLocalMutation } from "../db/syncEngine";
import { useEntityRecords } from "../db/useLocalData";
import {
  calcularSaldoPropagacion,
  calcularSupervivenciaBolsa,
  calcularVivasEnBolsa,
} from "../domain/calculations";
import type {
  Propagacion,
  RevisionBolsa,
  TransplanteBolsa,
  Ubicacion,
} from "../domain/types";

export const TransplanteBolsaPage: React.FC<{
  preselectedLoteId?: string | null;
  onClearPreselected?: () => void;
}> = ({ preselectedLoteId, onClearPreselected }) => {
  const { can, user } = useAuth();
  const canWrite = can("transplante_bolsa", "write");
  const canDelete = can("transplante_bolsa", "delete");

  const { rows: transplantes, loading: tpLoading } =
    useEntityRecords<TransplanteBolsa>("transplante_bolsa");
  const { rows: revisiones } = useEntityRecords<RevisionBolsa>("revisiones_bolsa");
  const { rows: propagaciones, loading: propLoading } =
    useEntityRecords<Propagacion>("propagacion");
  const { rows: ubicaciones, loading: ubLoading } = useEntityRecords<Ubicacion>("ubicaciones");

  const [tpOpen, setTpOpen] = useState(false);
  const [revModalTp, setRevModalTp] = useState<TransplanteBolsa | null>(null);
  const [tpErr, setTpErr] = useState("");
  const [revErr, setRevErr] = useState("");

  // Form Transplante a Bolsa
  const [loteId, setLoteId] = useState("");
  const [fechaTp, setFechaTp] = useState(new Date().toISOString().slice(0, 10));
  const [ubicacionId, setUbicacionId] = useState("");
  const [camaMesa, setCamaMesa] = useState("Mesa B1");
  const [cantProcesada, setCantProcesada] = useState("50");
  const [cantBuenas, setCantBuenas] = useState("45");
  const [tipoLote, setTipoLote] = useState<"PLANTA_COMERCIAL" | "PLANTA_MADRE">("PLANTA_COMERCIAL");
  const [promoverMadre, setPromoverMadre] = useState(true);
  const [capBolsa, setCapBolsa] = useState("1L");
  const [obsTp, setObsTp] = useState("");

  // Form Revisión Periódica CV-05
  const [revFecha, setRevFecha] = useState(new Date().toISOString().slice(0, 10));
  const [revFase, setRevFase] = useState<RevisionBolsa["fase"]>("ENRAIZAMIENTO");
  const [revBuenos, setRevBuenos] = useState("40");
  const [revMalos, setRevMalos] = useState("2");
  const [revComp, setRevComp] = useState("Ninguna");
  const [revEstado, setRevEstado] = useState<RevisionBolsa["estado_sanitario"]>("OPTIMO");
  const [revObs, setRevObs] = useState("");

  const propMap = useMemo(() => new Map(propagaciones.map((p) => [p.id, p])), [propagaciones]);
  const ubMap = useMemo(() => new Map(ubicaciones.map((u) => [u.id, u.nombre])), [ubicaciones]);

  const openNewTransplante = (initialLoteId?: string) => {
    const candidateLotes = propagaciones.filter(
      (p) => calcularSaldoPropagacion(p, transplantes) > 0
    );
    const chosen = candidateLotes.find((c) => c.id === initialLoteId) || candidateLotes[0];
    const disp = chosen ? calcularSaldoPropagacion(chosen, transplantes) : 0;
    setLoteId(chosen?.id || "");
    setFechaTp(new Date().toISOString().slice(0, 10));
    setUbicacionId(ubicaciones[2]?.id || ubicaciones[0]?.id || "");
    setCamaMesa("Mesa B1");
    setCantProcesada(String(disp));
    setCantBuenas(String(disp));
    setTipoLote("PLANTA_COMERCIAL");
    setPromoverMadre(true);
    setCapBolsa("1L");
    setObsTp("");
    setTpErr("");
    setTpOpen(true);
  };

  useEffect(() => {
    if (preselectedLoteId && !tpLoading && !propLoading && !ubLoading) {
      openNewTransplante(preselectedLoteId);
      onClearPreselected?.();
    }
  }, [preselectedLoteId, tpLoading, propLoading, ubLoading]);

  const selectedLote = propMap.get(loteId);
  const saldoDisponibleLote = selectedLote
    ? calcularSaldoPropagacion(selectedLote, transplantes)
    : 0;

  const liveCalc = useMemo(() => {
    try {
      return {
        res: calcularSupervivenciaBolsa(
          saldoDisponibleLote,
          Number(cantProcesada || 0),
          Number(cantBuenas || 0)
        ),
        error: null,
      };
    } catch (e) {
      return { res: null, error: e instanceof Error ? e.message : "Datos inválidos" };
    }
  }, [saldoDisponibleLote, cantProcesada, cantBuenas]);

  const handleSaveTp = async (e: React.FormEvent) => {
    e.preventDefault();
    setTpErr("");
    if (!selectedLote) return setTpErr("Selecciona un lote con saldo disponible.");
    if (fechaTp < selectedLote.fecha_siembra) {
      return setTpErr("La fecha de trasplante no puede ser anterior a la siembra.");
    }
    if (!liveCalc.res || liveCalc.error) {
      return setTpErr(liveCalc.error || "Verifica las cantidades ingresadas.");
    }

    const tpId = crypto.randomUUID();
    const codigoTp = `TP-${selectedLote.codigo_lote}-${
      transplantes.filter((t) => t.lote_id === selectedLote.id).length + 1
    }`;

    await queueLocalMutation("transplante_bolsa", "CREATE", {
      id: tpId,
      lote_id: selectedLote.id,
      codigo_transplante: codigoTp,
      fecha_transplante: fechaTp,
      ubicacion_id: ubicacionId || ubicaciones[0]?.id,
      responsable_id: user?.funcionario_id || null,
      cama_o_mesa: camaMesa,
      cantidad_procesada: Number(cantProcesada),
      cantidad_buenas: Number(cantBuenas),
      cantidad_malas: liveCalc.res.cantidad_malas,
      porcentaje_buenas: liveCalc.res.porcentaje_buenas,
      porcentaje_malas: liveCalc.res.porcentaje_malas,
      alerta_merma: liveCalc.res.alerta_merma,
      tipo_lote: tipoLote,
      capacidad_bolsa: capBolsa,
      observaciones: obsTp,
      version: 1,
    });

    await db.propagacion.update(selectedLote.id, {
      estado_lote: liveCalc.res.nuevo_estado_lote,
    });

    if (tipoLote === "PLANTA_MADRE" && promoverMadre && Number(cantBuenas) > 0) {
      const lmId = crypto.randomUUID();
      const count = Number(cantBuenas);
      await queueLocalMutation("lotes_planta_madre", "CREATE", {
        id: lmId,
        lote_id: selectedLote.id,
        transplante_bolsa_id: tpId,
        fecha_establecimiento: fechaTp,
        ubicacion_id: ubicacionId || ubicaciones[0]?.id,
        cantidad_madres_inicial: count,
        cantidad_madres_activas: count,
        observaciones: `Promovido desde ${codigoTp}`,
        version: 1,
      });
      const units = Math.min(count, 20);
      for (let idx = 1; idx <= units; idx += 1) {
        await queueLocalMutation("unidades_planta_madre", "CREATE", {
          id: crypto.randomUUID(),
          lote_madre_id: lmId,
          numero_planta: idx,
          codigo_planta: `PM-${selectedLote.codigo_lote}-${String(idx).padStart(3, "0")}`,
          estado_planta: "ACTIVA",
          total_esquejes: 0,
          total_semillas: 0,
          observaciones: "",
          version: 1,
        });
      }
    }

    setTpOpen(false);
  };

  const handleSaveRev = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!revModalTp) return;
    setRevErr("");
    const buenos = Number(revBuenos);
    const malos = Number(revMalos);
    const revisadas = buenos + malos;
    if (revisadas <= 0) return setRevErr("Las unidades revisadas deben ser mayores a cero.");
    if (revFecha < revModalTp.fecha_transplante) {
      return setRevErr("La fecha de revisión no puede ser anterior al trasplante.");
    }
    const vivasPrevias = calcularVivasEnBolsa(revModalTp, revisiones);
    if (malos > vivasPrevias) {
      return setRevErr(
        `Las bajas nuevas (${malos}) superan el saldo vivo actual en bolsa (${vivasPrevias}).`
      );
    }

    await queueLocalMutation("revisiones_bolsa", "CREATE", {
      id: crypto.randomUUID(),
      transplante_id: revModalTp.id,
      fecha_revision: revFecha,
      fase: revFase,
      unidades_revisadas: revisadas,
      contador_buenos: buenos,
      contador_malos: malos,
      tipo_complicacion: revComp,
      estado_sanitario: revEstado,
      responsable_id: user?.funcionario_id || null,
      observaciones: revObs,
      version: 1,
    });
    setRevModalTp(null);
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900">
            Módulo 3: Transplante a Bolsa y Revisión Periódica
          </h1>
          <p className="text-xs sm:text-sm text-slate-600">
            Control de saldo por lote, cálculo de supervivencia/merma (&gt;20% alerta) y monitoreo
            CV-05.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <ExportToolbar
            title="Modulo_Transplante_Bolsa"
            columns={["Código", "Lote", "Fecha", "Tipo", "Procesado", "Buenas", "Malas", "% Buenas", "Vivas Hoy"]}
            rows={transplantes.map((t) => [
              t.codigo_transplante,
              propMap.get(t.lote_id)?.codigo_lote || t.lote_id,
              t.fecha_transplante,
              t.tipo_lote,
              t.cantidad_procesada,
              t.cantidad_buenas,
              t.cantidad_malas,
              t.porcentaje_buenas,
              calcularVivasEnBolsa(t, revisiones),
            ])}
          />
          {canWrite && (
            <button
              type="button"
              onClick={() => openNewTransplante()}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-leaf-700 text-white text-sm font-bold shadow"
            >
              <Plus className="w-4 h-4" /> Nuevo Transplante
            </button>
          )}
        </div>
      </div>

      {transplantes.length === 0 ? (
        <EmptyState
          title="Sin trasplantes a bolsa"
          subtitle="Trasplanta unidades desde un lote de Propagación disponible."
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {transplantes.map((t) => {
            const lote = propMap.get(t.lote_id);
            const vivasHoy = calcularVivasEnBolsa(t, revisiones);
            const revsCount = revisiones.filter((r) => r.transplante_id === t.id).length;

            return (
              <div
                key={t.id}
                className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm space-y-3"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-base font-extrabold text-slate-900">
                        {t.codigo_transplante}
                      </span>
                      {t.alerta_merma && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold bg-red-100 text-red-800">
                          <AlertTriangle className="w-3 h-3" /> Merma &gt;20%
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-slate-500">
                      Lote {lote?.codigo_lote || "N/A"} • {t.fecha_transplante} •{" "}
                      {ubMap.get(t.ubicacion_id) || "N/A"}
                    </div>
                  </div>
                  <SyncStatusBadge status={t._local_sync_status} />
                </div>

                <div className="grid grid-cols-2 gap-3 text-xs bg-slate-50 rounded-xl p-2.5 border border-slate-100">
                  <div>
                    <span className="text-slate-500">Tipo Lote</span>
                    <div className="font-bold text-slate-800 truncate">{t.tipo_lote}</div>
                  </div>
                  <div>
                    <span className="text-slate-500">Buenas / Malas</span>
                    <div className="font-bold text-slate-800">
                      {t.cantidad_buenas} / {t.cantidad_malas}
                    </div>
                  </div>
                  <div>
                    <span className="text-slate-500">Supervivencia</span>
                    <div
                      className={`font-extrabold ${
                        t.alerta_merma ? "text-red-700" : "text-emerald-700"
                      }`}
                    >
                      {t.porcentaje_buenas}%
                    </div>
                  </div>
                  <div>
                    <span className="text-slate-500">Vivas Hoy</span>
                    <div className="font-extrabold text-blue-700">{vivasHoy} uds</div>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setRevModalTp(t);
                      setRevFecha(new Date().toISOString().slice(0, 10));
                      setRevBuenos(String(Math.max(0, vivasHoy - 1)));
                      setRevMalos(vivasHoy > 0 ? "1" : "0");
                      setRevErr("");
                    }}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 text-white text-xs font-semibold"
                  >
                    <ClipboardCheck className="w-3.5 h-3.5" /> Revisión Periódica ({revsCount})
                  </button>
                  {canDelete && (
                    <button
                      type="button"
                      onClick={() => void queueLocalMutation("transplante_bolsa", "DELETE", { ...t })}
                      className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-red-200 text-xs font-semibold text-red-700"
                    >
                      <Trash2 className="w-3.5 h-3.5" /> Eliminar
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modal Nuevo Transplante a Bolsa */}
      <Modal
        open={tpOpen}
        onClose={() => setTpOpen(false)}
        title="Registrar Transplante a Bolsa"
        subtitle="Descuenta del saldo vivo de Propagación y clasifica hacia Madres o Comercial"
      >
        <form onSubmit={handleSaveTp} className="space-y-3 text-xs">
          {tpErr && (
            <div className="rounded-lg bg-red-50 border border-red-200 p-2.5 font-semibold text-red-800">
              {tpErr}
            </div>
          )}
          <div>
            <label htmlFor="tp-lote" className="block font-bold mb-1">Lote de Propagación con Saldo *</label>
            <select
              id="tp-lote"
              value={loteId}
              onChange={(e) => {
                const l = propMap.get(e.target.value);
                const d = l ? calcularSaldoPropagacion(l, transplantes) : 0;
                setLoteId(e.target.value);
                setCantProcesada(String(d));
                setCantBuenas(String(d));
              }}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 bg-white"
            >
              {propagaciones.map((p) => {
                const d = calcularSaldoPropagacion(p, transplantes);
                return (
                  <option key={p.id} value={p.id} disabled={d === 0}>
                    {p.codigo_lote} — Disponible: {d} uds ({p.estado_lote})
                  </option>
                );
              })}
            </select>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block font-bold mb-1">Fecha Transplante *</label>
              <input
                type="date"
                required
                value={fechaTp}
                onChange={(e) => setFechaTp(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2"
              />
            </div>
            <div>
              <label htmlFor="tp-tipo" className="block font-bold mb-1">Tipo de Lote *</label>
              <select
                id="tp-tipo"
                value={tipoLote}
                onChange={(e) => setTipoLote(e.target.value as TransplanteBolsa["tipo_lote"])}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 bg-white"
              >
                <option value="PLANTA_COMERCIAL">PLANTA_COMERCIAL</option>
                <option value="PLANTA_MADRE">PLANTA_MADRE</option>
              </select>
            </div>
            <div>
              <label htmlFor="tp-proc" className="block font-bold mb-1">
                Unidades a Bolsa (máx {saldoDisponibleLote}) *
              </label>
              <input
                id="tp-proc"
                type="number"
                min={1}
                max={saldoDisponibleLote}
                value={cantProcesada}
                onChange={(e) => setCantProcesada(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2"
              />
            </div>
            <div>
              <label htmlFor="tp-buenas" className="block font-bold mb-1">Cantidad Buenas Sobrevivientes *</label>
              <input
                id="tp-buenas"
                type="number"
                min={0}
                max={Number(cantProcesada || 0)}
                value={cantBuenas}
                onChange={(e) => setCantBuenas(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2"
              />
            </div>
            <div>
              <label className="block font-bold mb-1">Ubicación / Casa Malla</label>
              <select
                value={ubicacionId}
                onChange={(e) => setUbicacionId(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 bg-white"
              >
                {ubicaciones.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.nombre}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block font-bold mb-1">Mesa / Capacidad Bolsa</label>
              <div className="flex gap-2">
                <input
                  value={camaMesa}
                  onChange={(e) => setCamaMesa(e.target.value)}
                  className="flex-1 rounded-lg border border-slate-300 px-3 py-2"
                />
                <input
                  value={capBolsa}
                  onChange={(e) => setCapBolsa(e.target.value)}
                  className="w-16 rounded-lg border border-slate-300 px-2 py-2"
                />
              </div>
            </div>
          </div>

          {liveCalc.res && (
            <div
              className={`rounded-xl border p-3 font-semibold ${
                liveCalc.res.alerta_merma
                  ? "bg-red-50 border-red-200 text-red-900"
                  : "bg-emerald-50 border-emerald-200 text-emerald-900"
              }`}
            >
              Malas calculadas: <strong>{liveCalc.res.cantidad_malas}</strong> • Buenas:{" "}
              <strong>{liveCalc.res.porcentaje_buenas}%</strong> • Merma:{" "}
              <strong>{liveCalc.res.porcentaje_malas}%</strong>{" "}
              {liveCalc.res.alerta_merma ? "⚠️ ALERTA: MERMA > 20%" : "✓ Supervivencia normal"}
            </div>
          )}

          {tipoLote === "PLANTA_MADRE" && (
            <label className="flex items-center gap-2 font-bold text-slate-800 p-2 rounded-lg bg-slate-50 border border-slate-200">
              <input
                type="checkbox"
                checked={promoverMadre}
                onChange={(e) => setPromoverMadre(e.target.checked)}
                className="w-4 h-4"
              />
              Promover automáticamente al Módulo 2 (Planta Madre) con unidades numeradas
            </label>
          )}

          <div>
            <label className="block font-bold mb-1">Observaciones</label>
            <input
              value={obsTp}
              onChange={(e) => setObsTp(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
            />
          </div>

          <button
            type="submit"
            disabled={!liveCalc.res}
            className="w-full py-2.5 rounded-xl bg-leaf-700 text-white font-bold text-sm disabled:opacity-50"
          >
            Guardar Transplante a Bolsa
          </button>
        </form>
      </Modal>

      {/* Modal Revisión Periódica CV-05 */}
      <Modal
        open={Boolean(revModalTp)}
        onClose={() => setRevModalTp(null)}
        title={`Revisión Periódica en Bolsa (CV-05) — ${revModalTp?.codigo_transplante || ""}`}
        subtitle="Seguimiento fitosanitario en enraizamiento/bolsa con ajuste de saldo vivo"
        wide
      >
        <div className="space-y-4 text-xs">
          <div>
            <h3 className="font-bold text-slate-700 uppercase mb-1.5">Historial de Revisiones</h3>
            <div className="space-y-1.5 max-h-40 overflow-y-auto">
              {revisiones
                .filter((r) => r.transplante_id === revModalTp?.id)
                .map((r) => (
                  <div
                    key={r.id}
                    className="rounded-lg border border-slate-200 bg-slate-50 p-2 flex justify-between"
                  >
                    <span>
                      <strong>{r.fecha_revision}</strong> ({r.fase}) • {r.tipo_complicacion} [
                      {r.estado_sanitario}]
                    </span>
                    <span className="font-bold">
                      +{r.contador_buenos} buenas / -{r.contador_malos} bajas
                    </span>
                  </div>
                ))}
            </div>
          </div>

          {canWrite && (
            <form onSubmit={handleSaveRev} className="space-y-3 border-t border-slate-200 pt-3">
              {revErr && (
                <div className="rounded-lg bg-red-50 border border-red-200 p-2.5 font-semibold text-red-800">
                  {revErr}
                </div>
              )}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block font-bold mb-1">Fecha Revisión *</label>
                  <input
                    type="date"
                    required
                    value={revFecha}
                    onChange={(e) => setRevFecha(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2"
                  />
                </div>
                <div>
                  <label className="block font-bold mb-1">Fase</label>
                  <select
                    value={revFase}
                    onChange={(e) => setRevFase(e.target.value as RevisionBolsa["fase"])}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 bg-white"
                  >
                    <option value="ENRAIZAMIENTO">ENRAIZAMIENTO</option>
                    <option value="BOLSA_INICIAL">BOLSA_INICIAL</option>
                    <option value="ACLIMATACION">ACLIMATACION</option>
                  </select>
                </div>
                <div>
                  <label className="block font-bold mb-1">Estado Sanitario</label>
                  <select
                    value={revEstado}
                    onChange={(e) =>
                      setRevEstado(e.target.value as RevisionBolsa["estado_sanitario"])
                    }
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 bg-white"
                  >
                    <option value="OPTIMO">OPTIMO</option>
                    <option value="OBSERVACION">OBSERVACION</option>
                    <option value="CRITICO">CRITICO</option>
                  </select>
                </div>
                <div>
                  <label className="block font-bold mb-1">Contador Buenos *</label>
                  <input
                    type="number"
                    min={0}
                    value={revBuenos}
                    onChange={(e) => setRevBuenos(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2"
                  />
                </div>
                <div>
                  <label className="block font-bold mb-1">Contador Malos / Bajas *</label>
                  <input
                    type="number"
                    min={0}
                    value={revMalos}
                    onChange={(e) => setRevMalos(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2"
                  />
                </div>
                <div>
                  <label className="block font-bold mb-1">Complicación Fitosanitaria</label>
                  <input
                    value={revComp}
                    onChange={(e) => setRevComp(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2"
                  />
                </div>
              </div>
              <div>
                <label className="block font-bold mb-1">Observaciones de Campo</label>
                <input
                  value={revObs}
                  onChange={(e) => setRevObs(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2"
                />
              </div>
              <button
                type="submit"
                className="w-full py-2.5 rounded-xl bg-leaf-700 text-white font-bold text-sm"
              >
                Registrar Revisión Periódica
              </button>
            </form>
          )}
        </div>
      </Modal>
    </div>
  );
};
