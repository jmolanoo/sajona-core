import React, { useMemo, useState } from "react";
import { ChevronDown, ChevronUp, GitBranch, Plus, Scissors, Trees } from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { EmptyState, ExportToolbar, Modal, SyncStatusBadge } from "../components/UiPrimitives";
import { queueLocalMutation } from "../db/syncEngine";
import { useEntityRecords } from "../db/useLocalData";
import { calcularTotalesExtraccion } from "../domain/calculations";
import type {
  DetallePlantaExtraccion,
  ExtraccionMadre,
  LotePlantaMadre,
  Propagacion,
  Ubicacion,
  UnidadPlantaMadre,
  Variedad,
} from "../domain/types";

export const PlantaMadrePage: React.FC = () => {
  const { can, user } = useAuth();
  const canWrite = can("extracciones_madre", "write");

  const { rows: lotesMadre } = useEntityRecords<LotePlantaMadre>("lotes_planta_madre");
  const { rows: unidades } = useEntityRecords<UnidadPlantaMadre>("unidades_planta_madre");
  const { rows: extracciones } = useEntityRecords<ExtraccionMadre>("extracciones_madre");
  const { rows: propagaciones } = useEntityRecords<Propagacion>("propagacion");
  const { rows: variedades } = useEntityRecords<Variedad>("variedades");
  const { rows: ubicaciones } = useEntityRecords<Ubicacion>("ubicaciones");

  const [expandedLmId, setExpandedLmId] = useState<string | null>(null);
  const [extModalLm, setExtModalLm] = useState<LotePlantaMadre | null>(null);
  const [newLmOpen, setNewLmOpen] = useState(false);

  // Estado formulario extracción matricial CV-09
  const [fechaExtraccion, setFechaExtraccion] = useState(new Date().toISOString().slice(0, 10));
  const [derivHijo, setDerivHijo] = useState(true);
  const [codigoHijo, setCodigoHijo] = useState("");
  const [obsExt, setObsExt] = useState("");
  const [rowsExt, setRowsExt] = useState<DetallePlantaExtraccion[]>([]);
  const [extErr, setExtErr] = useState("");

  // Estado nuevo lote madre manual
  const [lmLoteId, setLmLoteId] = useState("");
  const [lmFecha, setLmFecha] = useState(new Date().toISOString().slice(0, 10));
  const [lmCant, setLmCant] = useState("4");
  const [lmUbId, setLmUbId] = useState("");
  const [lmErr, setLmErr] = useState("");

  const propMap = useMemo(() => new Map(propagaciones.map((p) => [p.id, p])), [propagaciones]);
  const varMap = useMemo(() => new Map(variedades.map((v) => [v.id, v.nombre])), [variedades]);

  const openExtraccionModal = (lm: LotePlantaMadre) => {
    const activeUnits = unidades
      .filter((u) => u.lote_madre_id === lm.id && u.estado_planta !== "DESCARTADA")
      .sort((a, b) => a.numero_planta - b.numero_planta);
    setExtModalLm(lm);
    setFechaExtraccion(new Date().toISOString().slice(0, 10));
    setDerivHijo(true);
    setCodigoHijo(`LOT-2026-${String(propagaciones.length + 34).padStart(3, "0")}`);
    setObsExt("");
    setExtErr("");
    setRowsExt(
      activeUnits.length > 0
        ? activeUnits.map((u) => ({
            unidad_id: u.id,
            numero_planta: u.numero_planta,
            esquejes: 0,
            semillas: 0,
          }))
        : [{ unidad_id: null, numero_planta: 1, esquejes: 0, semillas: 0 }]
    );
  };

  const totalesExt = useMemo(() => calcularTotalesExtraccion(rowsExt), [rowsExt]);

  const handleSaveExtraccion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!extModalLm) return;
    setExtErr("");

    if (fechaExtraccion < extModalLm.fecha_establecimiento) {
      return setExtErr(
        "La fecha de extracción no puede ser anterior a la fecha de establecimiento."
      );
    }
    const cleanRows = rowsExt.filter((r) => Number(r.esquejes) > 0 || Number(r.semillas) > 0);
    if (cleanRows.length === 0 || totalesExt.totalGeneral <= 0) {
      return setExtErr("Registra al menos 1 esqueje o 1 semilla en la tabla de plantas madre.");
    }
    if (derivHijo && !codigoHijo.trim()) {
      return setExtErr("Indica el Id Lote Hijo para derivar a Propagación.");
    }

    const extId = crypto.randomUUID();
    await queueLocalMutation("extracciones_madre", "CREATE", {
      id: extId,
      lote_madre_id: extModalLm.id,
      fecha_transplante_ref: extModalLm.fecha_establecimiento,
      fecha_extraccion: fechaExtraccion,
      responsable_id: user?.funcionario_id || null,
      detalle_plantas: cleanRows,
      total_esquejes: totalesExt.totalEsquejes,
      total_semillas: totalesExt.totalSemillas,
      lote_hijo_codigo: derivHijo ? codigoHijo.trim() : null,
      observaciones: obsExt,
      version: 1,
    });

    // Actualizar acumulados locales en cada Unidad Planta Madre involucrada
    for (const row of cleanRows) {
      if (!row.unidad_id) continue;
      const unit = unidades.find((u) => u.id === row.unidad_id);
      if (unit) {
        await queueLocalMutation("unidades_planta_madre", "UPDATE", {
          ...unit,
          total_esquejes: Number(unit.total_esquejes) + Number(row.esquejes),
          total_semillas: Number(unit.total_semillas) + Number(row.semillas),
          ultima_extraccion: fechaExtraccion,
          version: unit.version,
        });
      }
    }

    // Derivar nuevo lote hijo en Propagación en orden causal secuencial (funciona 100% offline!)
    const padre = propMap.get(extModalLm.lote_id);
    if (derivHijo && codigoHijo.trim() && padre) {
      await queueLocalMutation("propagacion", "CREATE", {
        id: crypto.randomUUID(),
        codigo_lote: codigoHijo.trim(),
        fecha_siembra: fechaExtraccion,
        variedad_id: padre.variedad_id,
        ubicacion_id: extModalLm.ubicacion_id || padre.ubicacion_id || null,
        responsable_id: user?.funcionario_id || null,
        tipo_propagacion: totalesExt.totalEsquejes >= totalesExt.totalSemillas ? "ESQUEJE" : "SEMILLA",
        tipo_incorporacion: "PROPIA",
        origen_extraccion_id: extId,
        proveedor: "",
        cantidad_material: totalesExt.totalGeneral,
        cantidad_plantas_madre: 0,
        bajas_propagacion: 0,
        estado_lote: "SIEMBRA",
        observaciones: `Derivado desde extracción en bloque madre ${padre.codigo_lote}`,
        version: 1,
      });
    }

    setExtModalLm(null);
  };

  const handleToggleUnitState = async (u: UnidadPlantaMadre, next: UnidadPlantaMadre["estado_planta"]) => {
    await queueLocalMutation("unidades_planta_madre", "UPDATE", {
      ...u,
      estado_planta: next,
    });
    const lm = lotesMadre.find((m) => m.id === u.lote_madre_id);
    if (lm) {
      const siblingUnits = unidades.filter((x) => x.lote_madre_id === lm.id);
      const activas = siblingUnits.filter((x) =>
        x.id === u.id ? next !== "DESCARTADA" : x.estado_planta !== "DESCARTADA"
      ).length;
      await queueLocalMutation("lotes_planta_madre", "UPDATE", {
        ...lm,
        cantidad_madres_activas: activas,
      });
    }
  };

  const handleCreateLoteMadre = async (e: React.FormEvent) => {
    e.preventDefault();
    setLmErr("");
    if (!lmLoteId) return setLmErr("Selecciona un lote base.");
    const cant = Number(lmCant);
    if (cant <= 0 || cant > 50) return setLmErr("Indica entre 1 y 50 unidades iniciales.");

    const lmId = crypto.randomUUID();
    const padre = propMap.get(lmLoteId);
    await queueLocalMutation("lotes_planta_madre", "CREATE", {
      id: lmId,
      lote_id: lmLoteId,
      transplante_bolsa_id: null,
      fecha_establecimiento: lmFecha,
      ubicacion_id: lmUbId || ubicaciones[0]?.id || null,
      cantidad_madres_inicial: cant,
      cantidad_madres_activas: cant,
      observaciones: "Lote madre registrado manualmente",
      version: 1,
    });

    for (let i = 1; i <= cant; i += 1) {
      await queueLocalMutation("unidades_planta_madre", "CREATE", {
        id: crypto.randomUUID(),
        lote_madre_id: lmId,
        numero_planta: i,
        codigo_planta: `PM-${padre?.codigo_lote || "LOTE"}-${String(i).padStart(3, "0")}`,
        estado_planta: "ACTIVA",
        total_esquejes: 0,
        total_semillas: 0,
        observaciones: "",
        version: 1,
      });
    }
    setNewLmOpen(false);
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900">
            Módulo 2: Planta Madre y Extracciones
          </h1>
          <p className="text-xs sm:text-sm text-slate-600">
            Gestión por unidad numerada (CV-02/03), matriz CV-09 de esquejes/semillas y derivación
            de lotes hijos.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <ExportToolbar
            title="Modulo_Planta_Madre"
            columns={["Lote Origen", "Establecimiento", "Madres Inicial", "Activas", "Esquejes", "Semillas"]}
            rows={lotesMadre.map((lm) => {
              const exts = extracciones.filter((e) => e.lote_madre_id === lm.id);
              return [
                propMap.get(lm.lote_id)?.codigo_lote || lm.lote_id,
                lm.fecha_establecimiento,
                lm.cantidad_madres_inicial,
                lm.cantidad_madres_activas,
                exts.reduce((a, e) => a + e.total_esquejes, 0),
                exts.reduce((a, e) => a + e.total_semillas, 0),
              ];
            })}
          />
          {canWrite && (
            <button
              type="button"
              onClick={() => {
                setLmLoteId(propagaciones[0]?.id || "");
                setLmUbId(ubicaciones[1]?.id || ubicaciones[0]?.id || "");
                setNewLmOpen(true);
              }}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-leaf-700 text-white text-sm font-bold shadow"
            >
              <Plus className="w-4 h-4" /> Nuevo Bloque Madre
            </button>
          )}
        </div>
      </div>

      {lotesMadre.length === 0 ? (
        <EmptyState
          title="Sin lotes de Planta Madre"
          subtitle="Promueve un transplante a bolsa como PLANTA_MADRE o registra un nuevo bloque madre."
        />
      ) : (
        <div className="space-y-3">
          {lotesMadre.map((lm) => {
            const padre = propMap.get(lm.lote_id);
            const varName = padre ? varMap.get(padre.variedad_id) || "N/A" : "N/A";
            const lmUnits = unidades
              .filter((u) => u.lote_madre_id === lm.id)
              .sort((a, b) => a.numero_planta - b.numero_planta);
            const lmExts = extracciones.filter((e) => e.lote_madre_id === lm.id);
            const sumEsq = lmExts.reduce((a, e) => a + e.total_esquejes, 0);
            const sumSem = lmExts.reduce((a, e) => a + e.total_semillas, 0);
            const isOpen = expandedLmId === lm.id;

            return (
              <div
                key={lm.id}
                className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm space-y-3"
              >
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <Trees className="w-5 h-5 text-brand-800" />
                      <span className="text-base font-extrabold text-slate-900">
                        Bloque {padre?.codigo_lote || lm.lote_id.slice(0, 8)}
                      </span>
                      <SyncStatusBadge status={lm._local_sync_status} />
                    </div>
                    <p className="text-xs text-slate-600 mt-0.5">
                      {varName} • Establecido: <strong>{lm.fecha_establecimiento}</strong> • Activas:{" "}
                      <strong>
                        {lm.cantidad_madres_activas}/{lm.cantidad_madres_inicial}
                      </strong>{" "}
                      • Acumulado: <strong>{sumEsq} esquejes</strong> /{" "}
                      <strong>{sumSem} semillas</strong>
                    </p>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {canWrite && (
                      <button
                        type="button"
                        onClick={() => openExtraccionModal(lm)}
                        className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-brand-800 text-white text-xs font-bold shadow"
                      >
                        <Scissors className="w-4 h-4" /> Crear Esqueje / Semilla
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => setExpandedLmId(isOpen ? null : lm.id)}
                      className="inline-flex items-center gap-1 px-3 py-2 rounded-xl border border-slate-300 text-xs font-semibold text-slate-700"
                    >
                      {isOpen ? (
                        <>
                          Ocultar detalle <ChevronUp className="w-4 h-4" />
                        </>
                      ) : (
                        <>
                          Ver unidades e historial ({lmUnits.length}){" "}
                          <ChevronDown className="w-4 h-4" />
                        </>
                      )}
                    </button>
                  </div>
                </div>

                {isOpen && (
                  <div className="border-t border-slate-200 pt-3 grid grid-cols-1 lg:grid-cols-2 gap-4">
                    <div>
                      <h3 className="text-xs font-bold text-slate-700 uppercase mb-2">
                        Unidades Planta Madre ({lmUnits.length})
                      </h3>
                      <div className="space-y-1.5 max-h-64 overflow-y-auto">
                        {lmUnits.map((u) => (
                          <div
                            key={u.id}
                            className="flex items-center justify-between gap-2 rounded-xl border border-slate-200 px-3 py-2 text-xs bg-slate-50"
                          >
                            <div>
                              <span className="font-bold text-slate-900">
                                #{u.numero_planta} ({u.codigo_planta})
                              </span>
                              <div className="text-[11px] text-slate-600">
                                Esq: {u.total_esquejes} • Sem: {u.total_semillas}
                                {u.ultima_extraccion ? ` • Últ: ${u.ultima_extraccion}` : ""}
                              </div>
                            </div>
                            {canWrite ? (
                              <select
                                aria-label={`Estado planta #${u.numero_planta}`}
                                value={u.estado_planta}
                                onChange={(e) =>
                                  void handleToggleUnitState(
                                    u,
                                    e.target.value as UnidadPlantaMadre["estado_planta"]
                                  )
                                }
                                className="rounded-lg border border-slate-300 px-2 py-1 text-xs bg-white font-semibold"
                              >
                                <option value="ACTIVA">ACTIVA</option>
                                <option value="REPOSO">REPOSO</option>
                                <option value="DESCARTADA">DESCARTADA</option>
                              </select>
                            ) : (
                              <span className="font-semibold">{u.estado_planta}</span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h3 className="text-xs font-bold text-slate-700 uppercase mb-2">
                        Historial de Extracciones ({lmExts.length})
                      </h3>
                      {lmExts.length === 0 ? (
                        <p className="text-xs text-slate-500">Sin extracciones registradas aún.</p>
                      ) : (
                        <div className="space-y-2 max-h-64 overflow-y-auto">
                          {lmExts.map((e) => (
                            <div
                              key={e.id}
                              className="rounded-xl border border-slate-200 p-2.5 text-xs bg-slate-50 space-y-1"
                            >
                              <div className="flex justify-between font-bold text-slate-900">
                                <span>{e.fecha_extraccion}</span>
                                <span>
                                  {e.total_esquejes} esq. / {e.total_semillas} sem.
                                </span>
                              </div>
                              {e.lote_hijo_codigo && (
                                <div className="inline-flex items-center gap-1 text-emerald-700 font-semibold">
                                  <GitBranch className="w-3.5 h-3.5" /> Derivó lote hijo:{" "}
                                  {e.lote_hijo_codigo}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Modal Matricial Extracción CV-09 */}
      <Modal
        open={Boolean(extModalLm)}
        onClose={() => setExtModalLm(null)}
        title={`Extracción de Esquejes y Semillas — ${
          extModalLm ? propMap.get(extModalLm.lote_id)?.codigo_lote || "" : ""
        }`}
        subtitle="Matriz fiel a CV-09 con cálculo exacto y derivación opcional a Propagación"
        wide
      >
        <form onSubmit={handleSaveExtraccion} className="space-y-3 text-xs">
          {extErr && (
            <div className="rounded-lg bg-red-50 border border-red-200 p-2.5 font-semibold text-red-800">
              {extErr}
            </div>
          )}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block font-bold mb-1">Fecha Transplante Base</label>
              <input
                disabled
                value={extModalLm?.fecha_establecimiento || ""}
                className="w-full rounded-lg border border-slate-200 bg-slate-100 px-3 py-2"
              />
            </div>
            <div>
              <label htmlFor="ext-fecha" className="block font-bold mb-1">
                Fecha de Extracción *
              </label>
              <input
                id="ext-fecha"
                type="date"
                required
                value={fechaExtraccion}
                onChange={(e) => setFechaExtraccion(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2"
              />
            </div>
          </div>

          <div className="overflow-x-auto border border-slate-200 rounded-xl">
            <table className="w-full text-left border-collapse">
              <thead className="bg-slate-100 text-slate-700 font-bold">
                <tr>
                  <th className="p-2.5">Número Planta Madre</th>
                  <th className="p-2.5">Cantidad Esquejes</th>
                  <th className="p-2.5">Cantidad Semillas</th>
                </tr>
              </thead>
              <tbody>
                {rowsExt.map((row, idx) => (
                  <tr key={row.numero_planta} className="border-t border-slate-200">
                    <td className="p-2.5 font-bold text-slate-900">Planta #{row.numero_planta}</td>
                    <td className="p-2">
                      <input
                        type="number"
                        min={0}
                        aria-label={`Esquejes planta ${row.numero_planta}`}
                        value={row.esquejes}
                        onChange={(e) => {
                          const v = Math.max(0, Number(e.target.value));
                          setRowsExt((prev) =>
                            prev.map((x, i) => (i === idx ? { ...x, esquejes: v } : x))
                          );
                        }}
                        className="w-24 rounded-lg border border-slate-300 px-2.5 py-1.5"
                      />
                    </td>
                    <td className="p-2">
                      <input
                        type="number"
                        min={0}
                        aria-label={`Semillas planta ${row.numero_planta}`}
                        value={row.semillas}
                        onChange={(e) => {
                          const v = Math.max(0, Number(e.target.value));
                          setRowsExt((prev) =>
                            prev.map((x, i) => (i === idx ? { ...x, semillas: v } : x))
                          );
                        }}
                        className="w-24 rounded-lg border border-slate-300 px-2.5 py-1.5"
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="grid grid-cols-2 gap-2 rounded-xl bg-emerald-50 border border-emerald-200 p-3 font-bold text-emerald-900">
            <div>Total Lote Esquejes: {totalesExt.totalEsquejes}</div>
            <div>Total Lote Semillas: {totalesExt.totalSemillas}</div>
          </div>

          <div className="rounded-xl border border-slate-200 p-3 space-y-2">
            <label className="flex items-center gap-2 font-bold text-slate-800">
              <input
                type="checkbox"
                checked={derivHijo}
                onChange={(e) => setDerivHijo(e.target.checked)}
                className="w-4 h-4"
              />
              Derivar automáticamente nuevo lote hijo en Propagación
            </label>
            {derivHijo && (
              <div>
                <label className="block font-semibold mb-1">Código Lote Hijo *</label>
                <input
                  value={codigoHijo}
                  onChange={(e) => setCodigoHijo(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2"
                />
              </div>
            )}
          </div>

          <div>
            <label className="block font-bold mb-1">Observaciones</label>
            <input
              value={obsExt}
              onChange={(e) => setObsExt(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
            />
          </div>

          <button
            type="submit"
            className="w-full py-2.5 rounded-xl bg-leaf-700 text-white font-bold text-sm"
          >
            Guardar Extracción
          </button>
        </form>
      </Modal>

      {/* Modal Nuevo Bloque Madre */}
      <Modal
        open={newLmOpen}
        onClose={() => setNewLmOpen(false)}
        title="Registrar Bloque de Planta Madre"
        subtitle="Crea un bloque madre con sus plantas individuales numeradas"
      >
        <form onSubmit={handleCreateLoteMadre} className="space-y-3 text-xs">
          {lmErr && (
            <div className="rounded-lg bg-red-50 border border-red-200 p-2.5 text-red-800 font-semibold">
              {lmErr}
            </div>
          )}
          <div>
            <label className="block font-bold mb-1">Lote Propagación Origen *</label>
            <select
              value={lmLoteId}
              onChange={(e) => setLmLoteId(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 bg-white"
            >
              {propagaciones.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.codigo_lote} ({varMap.get(p.variedad_id) || "N/A"})
                </option>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-bold mb-1">Fecha Establecimiento *</label>
              <input
                type="date"
                value={lmFecha}
                onChange={(e) => setLmFecha(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2"
              />
            </div>
            <div>
              <label className="block font-bold mb-1">Cantidad Unidades *</label>
              <input
                type="number"
                min={1}
                max={50}
                value={lmCant}
                onChange={(e) => setLmCant(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2"
              />
            </div>
          </div>
          <div>
            <label className="block font-bold mb-1">Ubicación</label>
            <select
              value={lmUbId}
              onChange={(e) => setLmUbId(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 bg-white"
            >
              {ubicaciones.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.nombre}
                </option>
              ))}
            </select>
          </div>
          <button
            type="submit"
            className="w-full py-2.5 rounded-xl bg-leaf-700 text-white font-bold text-sm"
          >
            Guardar Bloque Madre
          </button>
        </form>
      </Modal>
    </div>
  );
};
