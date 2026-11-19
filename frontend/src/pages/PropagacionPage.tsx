import React, { useMemo, useState } from "react";
import { ArrowRightCircle, Eye, Pencil, Plus, Search, Trash2 } from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { EmptyState, ExportToolbar, Modal, SyncStatusBadge } from "../components/UiPrimitives";
import { queueLocalMutation } from "../db/syncEngine";
import { useEntityRecords } from "../db/useLocalData";
import { calcularSaldoPropagacion } from "../domain/calculations";
import type {
  Propagacion,
  TransplanteBolsa,
  Ubicacion,
  Variedad,
} from "../domain/types";

export const PropagacionPage: React.FC<{
  onSendToBolsa: (loteId: string) => void;
  onInspectLot: (lote: Propagacion) => void;
}> = ({ onSendToBolsa, onInspectLot }) => {
  const { can, user } = useAuth();
  const canWrite = can("propagacion", "write");
  const canDelete = can("propagacion", "delete");

  const { rows: lotes } = useEntityRecords<Propagacion>("propagacion");
  const { rows: transplantes } = useEntityRecords<TransplanteBolsa>("transplante_bolsa");
  const { rows: variedades } = useEntityRecords<Variedad>("variedades");
  const { rows: ubicaciones } = useEntityRecords<Ubicacion>("ubicaciones");

  const [query, setQuery] = useState("");
  const [estadoFiltro, setEstadoFiltro] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Propagacion | null>(null);
  const [formErr, setFormErr] = useState("");

  const [codigoLote, setCodigoLote] = useState("");
  const [fechaSiembra, setFechaSiembra] = useState(new Date().toISOString().slice(0, 10));
  const [variedadId, setVariedadId] = useState("");
  const [ubicacionId, setUbicacionId] = useState("");
  const [tipoProp, setTipoProp] = useState<"ESQUEJE" | "SEMILLA" | "IN_VITRO">("ESQUEJE");
  const [tipoInc, setTipoInc] = useState<"PROPIA" | "COMPRADA">("PROPIA");
  const [proveedor, setProveedor] = useState("");
  const [cantidadMaterial, setCantidadMaterial] = useState("100");
  const [cantidadMadresEst, setCantidadMadresEst] = useState("0");
  const [bajasProp, setBajasProp] = useState("0");
  const [observaciones, setObservaciones] = useState("");

  const varMap = useMemo(() => new Map(variedades.map((v) => [v.id, v.nombre])), [variedades]);

  const filtered = useMemo(
    () =>
      lotes.filter((l) => {
        if (estadoFiltro && l.estado_lote !== estadoFiltro) return false;
        if (!query.trim()) return true;
        const q = query.toLowerCase();
        const vName = (varMap.get(l.variedad_id) || "").toLowerCase();
        return (
          l.codigo_lote.toLowerCase().includes(q) ||
          vName.includes(q) ||
          l.tipo_propagacion.toLowerCase().includes(q)
        );
      }),
    [lotes, query, estadoFiltro, varMap]
  );

  const openNew = () => {
    setEditing(null);
    setCodigoLote(`LOT-2026-${String(lotes.length + 34).padStart(3, "0")}`);
    setFechaSiembra(new Date().toISOString().slice(0, 10));
    setVariedadId(variedades[0]?.id || "");
    setUbicacionId(ubicaciones[0]?.id || "");
    setTipoProp("ESQUEJE");
    setTipoInc("PROPIA");
    setProveedor("");
    setCantidadMaterial("100");
    setCantidadMadresEst("0");
    setBajasProp("0");
    setObservaciones("");
    setFormErr("");
    setModalOpen(true);
  };

  const openEdit = (lote: Propagacion) => {
    setEditing(lote);
    setCodigoLote(lote.codigo_lote);
    setFechaSiembra(lote.fecha_siembra);
    setVariedadId(lote.variedad_id);
    setUbicacionId(lote.ubicacion_id || "");
    setTipoProp(lote.tipo_propagacion);
    setTipoInc(lote.tipo_incorporacion);
    setProveedor(lote.proveedor || "");
    setCantidadMaterial(String(lote.cantidad_material));
    setCantidadMadresEst(String(lote.cantidad_plantas_madre));
    setBajasProp(String(lote.bajas_propagacion));
    setObservaciones(lote.observaciones || "");
    setFormErr("");
    setModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormErr("");
    const cant = Number(cantidadMaterial);
    const madresEst = Number(cantidadMadresEst);
    const bajas = Number(bajasProp);

    if (!codigoLote.trim()) return setFormErr("El Id Lote es obligatorio.");
    if (
      lotes.some(
        (l) => l.codigo_lote.toLowerCase() === codigoLote.trim().toLowerCase() && l.id !== editing?.id
      )
    ) {
      return setFormErr("Ya existe otro lote con ese código.");
    }
    if (!variedadId) return setFormErr("Selecciona una variedad.");
    if (cant <= 0) return setFormErr("La cantidad de material debe ser mayor a cero.");
    if (madresEst < 0 || madresEst > cant) {
      return setFormErr("Las plantas madre estimadas no pueden superar el material sembrado.");
    }
    if (bajas < 0 || bajas >= cant) {
      return setFormErr("Las bajas en cámara deben ser menores a la cantidad sembrada.");
    }
    if (tipoInc === "COMPRADA" && !proveedor.trim()) {
      return setFormErr("Para incorporación COMPRADA debes indicar el proveedor.");
    }

    const procesado = editing
      ? transplantes
          .filter((t) => t.lote_id === editing.id)
          .reduce((a, t) => a + Number(t.cantidad_procesada || 0), 0)
      : 0;
    const nuevoSaldo = cant - bajas - procesado;
    if (nuevoSaldo < 0) {
      return setFormErr("La cantidad sembrada menos bajas no cubre lo ya trasplantado a bolsa.");
    }
    const estadoLote: Propagacion["estado_lote"] =
      nuevoSaldo === 0 ? "FINALIZADO" : procesado > 0 ? "EN_TRANSPLANTE" : "SIEMBRA";

    await queueLocalMutation("propagacion", editing ? "UPDATE" : "CREATE", {
      ...(editing || {}),
      id: editing?.id || crypto.randomUUID(),
      codigo_lote: codigoLote.trim(),
      fecha_siembra: fechaSiembra,
      variedad_id: variedadId,
      ubicacion_id: ubicacionId || null,
      responsable_id: user?.funcionario_id || null,
      tipo_propagacion: tipoProp,
      tipo_incorporacion: tipoInc,
      origen_extraccion_id: editing?.origen_extraccion_id || null,
      proveedor: tipoInc === "COMPRADA" ? proveedor.trim() : "",
      cantidad_material: cant,
      cantidad_plantas_madre: madresEst,
      bajas_propagacion: bajas,
      estado_lote: estadoLote,
      observaciones,
      version: editing?.version || 1,
    });
    setModalOpen(false);
  };

  const handleDelete = async (lote: Propagacion) => {
    const tieneTrans = transplantes.some((t) => t.lote_id === lote.id);
    if (tieneTrans) {
      window.alert("No se puede eliminar un lote que ya registra trasplantes a bolsa activos.");
      return;
    }
    await queueLocalMutation("propagacion", "DELETE", { ...lote });
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900">
            Módulo 1: Propagación
          </h1>
          <p className="text-xs sm:text-sm text-slate-600">
            Registro de siembra por lote, origen genético, bajas iniciales y saldo disponible para
            bolsa.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <ExportToolbar
            title="Modulo_Propagacion"
            columns={["Id Lote", "Siembra", "Variedad", "Propagación", "Incorporación", "Sembrado", "Saldo", "Estado"]}
            rows={filtered.map((l) => [
              l.codigo_lote,
              l.fecha_siembra,
              varMap.get(l.variedad_id) || "N/A",
              l.tipo_propagacion,
              l.tipo_incorporacion,
              l.cantidad_material,
              calcularSaldoPropagacion(l, transplantes),
              l.estado_lote,
            ])}
          />
          {canWrite && (
            <button
              type="button"
              onClick={openNew}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-leaf-700 text-white text-sm font-bold shadow"
            >
              <Plus className="w-4 h-4" /> Nuevo
            </button>
          )}
        </div>
      </div>

      {/* Filtros */}
      <div className="bg-white rounded-2xl border border-slate-200 p-3 flex flex-col sm:flex-row gap-2">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3.5" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Buscar por lote, variedad o tipo de propagación..."
            className="w-full rounded-xl border border-slate-300 pl-9 pr-3 py-2 text-sm"
          />
        </div>
        <select
          aria-label="Filtrar por estado de lote"
          value={estadoFiltro}
          onChange={(e) => setEstadoFiltro(e.target.value)}
          className="rounded-xl border border-slate-300 px-3 py-2 text-sm bg-white"
        >
          <option value="">Todos los estados</option>
          <option value="SIEMBRA">SIEMBRA</option>
          <option value="EN_TRANSPLANTE">EN_TRANSPLANTE</option>
          <option value="FINALIZADO">FINALIZADO</option>
        </select>
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          title="Sin lotes registrados"
          subtitle="Registra un nuevo lote de siembra incluso sin conexión a Internet."
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {filtered.map((l) => {
            const saldo = calcularSaldoPropagacion(l, transplantes);
            return (
              <div
                key={l.id}
                className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm flex flex-col justify-between space-y-3"
              >
                <div className="space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="text-base font-extrabold text-slate-900">{l.codigo_lote}</div>
                      <div className="text-xs text-slate-500">
                        {varMap.get(l.variedad_id) || "N/A"} • {l.fecha_siembra}
                      </div>
                    </div>
                    <SyncStatusBadge status={l._local_sync_status} />
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs bg-slate-50 rounded-xl p-2.5 border border-slate-100">
                    <div>
                      <span className="text-slate-500">Tipo / Origen</span>
                      <div className="font-bold text-slate-800">
                        {l.tipo_propagacion} • {l.tipo_incorporacion}
                      </div>
                    </div>
                    <div>
                      <span className="text-slate-500">Estado</span>
                      <div className="font-bold text-slate-800">{l.estado_lote}</div>
                    </div>
                    <div>
                      <span className="text-slate-500">Sembrado / Bajas</span>
                      <div className="font-bold text-slate-800">
                        {l.cantidad_material} / {l.bajas_propagacion}
                      </div>
                    </div>
                    <div>
                      <span className="text-slate-500">Saldo Disponible</span>
                      <div className="font-extrabold text-emerald-700">{saldo} uds</div>
                    </div>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2 pt-1">
                  <button
                    type="button"
                    onClick={() => onInspectLot(l)}
                    className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700"
                  >
                    <Eye className="w-3.5 h-3.5" /> Traza
                  </button>
                  {canWrite && saldo > 0 && (
                    <button
                      type="button"
                      onClick={() => onSendToBolsa(l.id)}
                      className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-blue-700 text-white text-xs font-semibold"
                    >
                      <ArrowRightCircle className="w-3.5 h-3.5" /> A Bolsa
                    </button>
                  )}
                  {canWrite && (
                    <button
                      type="button"
                      onClick={() => openEdit(l)}
                      className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700"
                    >
                      <Pencil className="w-3.5 h-3.5" /> Editar
                    </button>
                  )}
                  {canDelete && (
                    <button
                      type="button"
                      onClick={() => void handleDelete(l)}
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

      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editing ? `Editar Lote ${editing.codigo_lote}` : "Nuevo Lote de Propagación"}
        subtitle="Validación biológica en cliente y servidor (funciona sin conexión)"
      >
        <form onSubmit={handleSave} className="space-y-3 text-xs">
          {formErr && (
            <div className="rounded-lg bg-red-50 border border-red-200 p-2.5 font-semibold text-red-800">
              {formErr}
            </div>
          )}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label htmlFor="prop-lote" className="block font-bold mb-1">
                Id Lote *
              </label>
              <input
                id="prop-lote"
                required
                value={codigoLote}
                onChange={(e) => setCodigoLote(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2"
              />
            </div>
            <div>
              <label htmlFor="prop-fecha" className="block font-bold mb-1">
                Fecha Siembra *
              </label>
              <input
                id="prop-fecha"
                type="date"
                required
                value={fechaSiembra}
                onChange={(e) => setFechaSiembra(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2"
              />
            </div>
            <div>
              <label htmlFor="prop-var" className="block font-bold mb-1">
                Variedad *
              </label>
              <select
                id="prop-var"
                value={variedadId}
                onChange={(e) => setVariedadId(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 bg-white"
              >
                {variedades.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.nombre}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="prop-ub" className="block font-bold mb-1">
                Ubicación
              </label>
              <select
                id="prop-ub"
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
              <label htmlFor="prop-tipo" className="block font-bold mb-1">
                Tipo Propagación
              </label>
              <select
                id="prop-tipo"
                value={tipoProp}
                onChange={(e) => setTipoProp(e.target.value as Propagacion["tipo_propagacion"])}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 bg-white"
              >
                <option value="ESQUEJE">ESQUEJE</option>
                <option value="SEMILLA">SEMILLA</option>
                <option value="IN_VITRO">IN_VITRO</option>
              </select>
            </div>
            <div>
              <label htmlFor="prop-inc" className="block font-bold mb-1">
                Incorporación
              </label>
              <select
                id="prop-inc"
                value={tipoInc}
                onChange={(e) => setTipoInc(e.target.value as Propagacion["tipo_incorporacion"])}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 bg-white"
              >
                <option value="PROPIA">PROPIA</option>
                <option value="COMPRADA">COMPRADA</option>
              </select>
            </div>
            {tipoInc === "COMPRADA" && (
              <div className="sm:col-span-2">
                <label htmlFor="prop-prov" className="block font-bold mb-1">
                  Proveedor / Vivero Origen *
                </label>
                <input
                  id="prop-prov"
                  value={proveedor}
                  onChange={(e) => setProveedor(e.target.value)}
                  placeholder="Nombre del proveedor autorizado"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2"
                />
              </div>
            )}
            <div>
              <label htmlFor="prop-cant" className="block font-bold mb-1">
                Cantidad de Siembra *
              </label>
              <input
                id="prop-cant"
                type="number"
                min={1}
                required
                value={cantidadMaterial}
                onChange={(e) => setCantidadMaterial(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2"
              />
            </div>
            <div>
              <label htmlFor="prop-bajas" className="block font-bold mb-1">
                Bajas en Propagación
              </label>
              <input
                id="prop-bajas"
                type="number"
                min={0}
                value={bajasProp}
                onChange={(e) => setBajasProp(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2"
              />
            </div>
            <div>
              <label htmlFor="prop-madres" className="block font-bold mb-1">
                Plantas Madre Estimadas
              </label>
              <input
                id="prop-madres"
                type="number"
                min={0}
                value={cantidadMadresEst}
                onChange={(e) => setCantidadMadresEst(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2"
              />
            </div>
            <div className="sm:col-span-2">
              <label htmlFor="prop-obs" className="block font-bold mb-1">
                Observaciones
              </label>
              <textarea
                id="prop-obs"
                rows={2}
                value={observaciones}
                onChange={(e) => setObservaciones(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2"
              />
            </div>
          </div>
          <button
            type="submit"
            className="w-full py-2.5 rounded-xl bg-leaf-700 text-white font-bold text-sm"
          >
            Guardar
          </button>
        </form>
      </Modal>
    </div>
  );
};
