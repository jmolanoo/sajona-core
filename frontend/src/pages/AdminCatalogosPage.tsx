import React, { useEffect, useState } from "react";
import { Plus } from "lucide-react";
import { apiClient } from "../api/client";
import { queueLocalMutation } from "../db/syncEngine";
import { useEntityRecords, useOnlineStatus } from "../db/useLocalData";
import type { Ubicacion, Variedad } from "../domain/types";

export const AdminCatalogosPage: React.FC = () => {
  const online = useOnlineStatus();
  const { rows: variedades } = useEntityRecords<Variedad>("variedades");
  const { rows: ubicaciones } = useEntityRecords<Ubicacion>("ubicaciones");

  const [varName, setVarName] = useState("");
  const [varQuim, setVarQuim] = useState("Alto CBD");
  const [ubName, setUbName] = useState("");
  const [ubTipo, setUbTipo] = useState<Ubicacion["tipo"]>("INVERNADERO");
  const [auditLogs, setAuditLogs] = useState<Array<Record<string, unknown>>>([]);

  useEffect(() => {
    if (online) {
      void apiClient
        .request<Array<Record<string, unknown>>>("/api/v1/admin/audit-logs?limit=25")
        .then(setAuditLogs)
        .catch(() => undefined);
    }
  }, [online]);

  const addVariedad = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!varName.trim()) return;
    await queueLocalMutation("variedades", "CREATE", {
      nombre: varName.trim(),
      quimiotipo: varQuim,
      dias_vegetativo_est: 21,
      dias_floracion_est: 56,
      descripcion: "",
      activo: true,
    });
    setVarName("");
  };

  const addUbicacion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ubName.trim()) return;
    await queueLocalMutation("ubicaciones", "CREATE", {
      nombre: ubName.trim(),
      tipo: ubTipo,
      capacidad_unidades: 500,
      activo: true,
    });
    setUbName("");
  };

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-extrabold text-slate-900">
          Catálogos de Soporte y Bitácora de Auditoría
        </h1>
        <p className="text-xs text-slate-600">
          Administración exclusiva de parámetros maestros (Variedades, Ubicaciones) y trazabilidad
          append-only.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-white rounded-2xl border border-slate-200 p-4 space-y-3">
          <h2 className="text-sm font-bold text-slate-900">Variedades ({variedades.length})</h2>
          <form onSubmit={addVariedad} className="flex flex-wrap gap-2 text-xs">
            <input
              value={varName}
              onChange={(e) => setVarName(e.target.value)}
              placeholder="Nueva variedad..."
              className="flex-1 rounded-lg border border-slate-300 px-3 py-2"
            />
            <input
              value={varQuim}
              onChange={(e) => setVarQuim(e.target.value)}
              placeholder="Quimiotipo"
              className="w-32 rounded-lg border border-slate-300 px-3 py-2"
            />
            <button
              type="submit"
              className="inline-flex items-center gap-1 px-3 py-2 rounded-lg bg-leaf-700 text-white font-bold"
            >
              <Plus className="w-4 h-4" /> Agregar
            </button>
          </form>
          <div className="space-y-1.5 text-xs">
            {variedades.map((v) => (
              <div key={v.id} className="rounded-lg bg-slate-50 border border-slate-200 px-3 py-2 flex justify-between">
                <span className="font-bold">{v.nombre}</span>
                <span className="text-slate-600">{v.quimiotipo}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-4 space-y-3">
          <h2 className="text-sm font-bold text-slate-900">Ubicaciones ({ubicaciones.length})</h2>
          <form onSubmit={addUbicacion} className="flex flex-wrap gap-2 text-xs">
            <input
              value={ubName}
              onChange={(e) => setUbName(e.target.value)}
              placeholder="Nombre zona..."
              className="flex-1 rounded-lg border border-slate-300 px-3 py-2"
            />
            <select
              value={ubTipo}
              onChange={(e) => setUbTipo(e.target.value as Ubicacion["tipo"])}
              className="rounded-lg border border-slate-300 px-2 py-2 bg-white"
            >
              <option value="INVERNADERO">INVERNADERO</option>
              <option value="CASA_MALLA">CASA_MALLA</option>
              <option value="CUBICULO">CUBICULO</option>
              <option value="ENRAIZAMIENTO">ENRAIZAMIENTO</option>
            </select>
            <button
              type="submit"
              className="inline-flex items-center gap-1 px-3 py-2 rounded-lg bg-leaf-700 text-white font-bold"
            >
              <Plus className="w-4 h-4" /> Agregar
            </button>
          </form>
          <div className="space-y-1.5 text-xs">
            {ubicaciones.map((u) => (
              <div key={u.id} className="rounded-lg bg-slate-50 border border-slate-200 px-3 py-2 flex justify-between">
                <span className="font-bold">{u.nombre}</span>
                <span className="text-slate-600">{u.tipo}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 p-4 space-y-2">
        <h2 className="text-sm font-bold text-slate-900">
          Bitácora de Auditoría Reciente ({auditLogs.length})
        </h2>
        <div className="space-y-1.5 max-h-64 overflow-y-auto text-xs">
          {auditLogs.map((log) => (
            <div
              key={String(log.id)}
              className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 flex flex-wrap justify-between gap-2"
            >
              <span>
                <strong>{String(log.username)}</strong> [{String(log.role)}] •{" "}
                {String(log.action)} en <strong>{String(log.entity_type)}</strong> (
                {String(log.source)})
              </span>
              <span className="text-slate-500">{String(log.created_at).slice(0, 19)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
